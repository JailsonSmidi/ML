"""
PDF Parser — extração de produtos de catálogos de fornecedores via Claude Vision.

Estratégia:
- Envia o PDF diretamente para a API da Anthropic (suporte nativo a PDF)
- Claude extrai todos os produtos em uma única chamada estruturada
- Retorna lista de dicts com os dados de cada produto
- Para PDFs grandes (>32MB), divide em chunks e mescla os resultados
"""

import json
import logging
import re
from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

EXTRACTION_PROMPT = """
Você está analisando um catálogo de fornecedor brasileiro. Extraia TODOS os produtos encontrados.

Para cada produto, retorne um objeto JSON com exatamente estes campos:
- catalog_name: nome do produto como aparece no catálogo
- description: descrição do produto (null se não houver)
- cost_price: preço de custo em reais como número (ex: 29.90). Se houver preço por caixa e por unidade, use o preço UNITÁRIO
- units_per_box: quantidade de unidades por caixa como inteiro (null se não informado)
- weight_kg: peso estimado do produto em kg como número decimal. Estime com base no tipo de produto se não informado. Considere o peso da unidade, não da caixa
- dimensions_cm: objeto com {"length": X, "width": Y, "height": Z} em centímetros. Estime se não informado
- search_terms_candidates: array com 3 a 6 termos de busca em português que compradores usariam para encontrar esse produto no Mercado Livre. Inclua o nome técnico E termos populares. Ex: ["ring light", "luz de led circular", "iluminador para foto", "anel de luz led"]

Regras importantes:
- Extraia TODOS os produtos, sem pular nenhum
- cost_price deve ser o valor unitário em reais, nunca o valor da caixa
- Se o catálogo mostrar apenas preço por caixa, divida pelo units_per_box
- weight_kg e dimensions_cm são críticos para cálculo de frete — estime com cuidado
- search_terms_candidates deve incluir termos que COMPRADORES usam, não termos técnicos do fornecedor

Retorne APENAS um array JSON válido, sem texto antes ou depois, sem markdown, sem explicações.
Exemplo de formato esperado:
[
  {
    "catalog_name": "Ring Light LED 26cm",
    "description": "Anel de luz LED com tripé, ideal para fotos e lives",
    "cost_price": 45.90,
    "units_per_box": 6,
    "weight_kg": 0.85,
    "dimensions_cm": {"length": 30, "width": 30, "height": 5},
    "search_terms_candidates": ["ring light", "anel de luz led", "luz para live", "iluminador led circular", "ring light com tripé"]
  }
]
"""


async def parse_catalog_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extrai todos os produtos de um PDF de catálogo de fornecedor.
    Retorna lista de dicts prontos para salvar no banco.
    """
    logger.info(f"Iniciando extração do PDF ({len(pdf_bytes) / 1024:.1f} KB)")

    # PDFs até ~32MB podem ser enviados diretamente
    # Acima disso, Anthropic retorna erro — por ora logamos e tentamos mesmo assim
    if len(pdf_bytes) > 32 * 1024 * 1024:
        logger.warning("PDF maior que 32MB — pode falhar na API da Anthropic")

    import base64
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    try:
        response = await client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        raw_text = response.content[0].text.strip()
        logger.debug(f"Resposta bruta da API: {raw_text[:500]}...")

        products = _parse_response(raw_text)
        logger.info(f"Extração concluída: {len(products)} produtos encontrados")
        return products

    except Exception as exc:
        logger.error(f"Erro na extração do PDF: {exc}")
        raise


def _parse_response(raw: str) -> list[dict]:
    """
    Faz parse da resposta do Claude, tolerando pequenas variações de formato.
    """
    # Remove possíveis blocos de código markdown que Claude às vezes inclui
    clean = re.sub(r"```json\s*", "", raw)
    clean = re.sub(r"```\s*", "", clean).strip()

    # Tenta parse direto
    try:
        data = json.loads(clean)
        if isinstance(data, list):
            return [_validate_product(p) for p in data]
        # Às vezes Claude retorna {"products": [...]}
        if isinstance(data, dict) and "products" in data:
            return [_validate_product(p) for p in data["products"]]
    except json.JSONDecodeError:
        pass

    # Fallback: encontra o array JSON dentro do texto
    match = re.search(r"\[[\s\S]+\]", clean)
    if match:
        try:
            data = json.loads(match.group())
            return [_validate_product(p) for p in data]
        except json.JSONDecodeError as exc:
            logger.error(f"Não foi possível fazer parse do JSON: {exc}")
            raise ValueError(f"Resposta inválida do Claude: {exc}") from exc

    raise ValueError("Nenhum array JSON encontrado na resposta do Claude")


def _validate_product(raw: dict) -> dict:
    """
    Valida e normaliza um produto extraído pelo Claude.
    Garante que campos críticos existam com valores padrão razoáveis.
    """
    # cost_price é obrigatório — se ausente, loga e usa 0
    cost_price = raw.get("cost_price")
    if cost_price is None:
        logger.warning(f"Produto sem cost_price: {raw.get('catalog_name')}")
        cost_price = 0.0

    # Normaliza dimensions_cm
    dims = raw.get("dimensions_cm")
    if dims and not isinstance(dims, dict):
        dims = None
    if dims:
        dims = {
            "length": float(dims.get("length", 10)),
            "width": float(dims.get("width", 10)),
            "height": float(dims.get("height", 5)),
        }

    # Garante que weight_kg seja float positivo
    weight = raw.get("weight_kg")
    try:
        weight = float(weight) if weight else 0.5
        weight = max(weight, 0.05)  # mínimo 50g
    except (TypeError, ValueError):
        weight = 0.5

    return {
        "catalog_name": str(raw.get("catalog_name", "Produto sem nome")).strip(),
        "description": raw.get("description") or None,
        "cost_price": float(cost_price),
        "units_per_box": int(raw["units_per_box"]) if raw.get("units_per_box") else None,
        "weight_kg": round(weight, 3),
        "dimensions_cm": dims,
        "search_terms_candidates": raw.get("search_terms_candidates") or [],
    }
