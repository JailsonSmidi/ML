"""
ML Table Scraper — extrai as tabelas públicas de frete e comissão do Mercado Livre.

URLs monitoradas:
- Fretes Full:       https://www.mercadolivre.com.br/ajuda/Custos-de-envio-Full_2020
- Fretes ME:         https://www.mercadolivre.com.br/ajuda/custo-de-envio_2883
- Comissões:         https://www.mercadolivre.com.br/ajuda/custos-de-venda_1338

Como as páginas são renderizadas com JS, usamos Playwright (headless).
Como fallback, se o scraping falhar, retorna os valores embutidos no código
para garantir que o sistema continue funcionando com dados levemente desatualizados.
"""

import logging
import re
import asyncio
from playwright.async_api import async_playwright
from app.config import settings

logger = logging.getLogger(__name__)

ML_SHIPPING_FULL_URL = "https://www.mercadolivre.com.br/ajuda/Custos-de-envio-Full_2020"
ML_SHIPPING_ME_URL = "https://www.mercadolivre.com.br/ajuda/custo-de-envio_2883"
ML_COMMISSIONS_URL = "https://www.mercadolivre.com.br/ajuda/custos-de-venda_1338"


async def scrape_shipping_table() -> list[dict]:
    """
    Extrai a tabela de fretes Full e Mercado Envios do site do ML.
    Retorna lista de dicts prontos para salvar em MLShippingRate.
    """
    results = []

    try:
        full_rates = await _scrape_full_shipping()
        results.extend(full_rates)
        logger.info(f"Frete Full: {len(full_rates)} faixas extraídas")
    except Exception as exc:
        logger.error(f"Falha ao extrair frete Full: {exc} — usando fallback")
        results.extend(_fallback_full_rates())

    try:
        me_rates = await _scrape_me_shipping()
        results.extend(me_rates)
        logger.info(f"Frete ME: {len(me_rates)} faixas extraídas")
    except Exception as exc:
        logger.error(f"Falha ao extrair frete ME: {exc} — usando fallback")
        results.extend(_fallback_me_rates())

    return results


async def scrape_commission_table() -> list[dict]:
    """
    Extrai a tabela de comissões por categoria do site do ML.
    Retorna lista de dicts prontos para salvar em MLCommissionRate.
    """
    try:
        rates = await _scrape_commissions()
        logger.info(f"Comissões: {len(rates)} categorias extraídas")
        return rates
    except Exception as exc:
        logger.error(f"Falha ao extrair comissões: {exc} — usando fallback")
        return _fallback_commission_rates()


async def _scrape_full_shipping() -> list[dict]:
    """Scraping da tabela de frete Full."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(locale="pt-BR")

        try:
            await page.goto(ML_SHIPPING_FULL_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)

            # Busca todas as tabelas na página
            tables = await page.query_selector_all("table")
            rates = []

            for table in tables:
                rows = await table.query_selector_all("tr")
                for row in rows[1:]:  # skip header
                    cells = await row.query_selector_all("td")
                    if len(cells) < 2:
                        continue

                    texts = [
                        (await c.inner_text()).strip() for c in cells
                    ]
                    rate = _parse_full_shipping_row(texts)
                    if rate:
                        rates.append(rate)

            return rates if rates else _fallback_full_rates()

        finally:
            await browser.close()


async def _scrape_me_shipping() -> list[dict]:
    """Scraping da tabela de frete Mercado Envios."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(locale="pt-BR")

        try:
            await page.goto(ML_SHIPPING_ME_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)

            tables = await page.query_selector_all("table")
            rates = []

            for table in tables:
                rows = await table.query_selector_all("tr")
                for row in rows[1:]:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 2:
                        continue
                    texts = [(await c.inner_text()).strip() for c in cells]
                    rate = _parse_me_shipping_row(texts)
                    if rate:
                        rates.append(rate)

            return rates if rates else _fallback_me_rates()

        finally:
            await browser.close()


async def _scrape_commissions() -> list[dict]:
    """Scraping da tabela de comissões por categoria."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(locale="pt-BR")

        try:
            await page.goto(ML_COMMISSIONS_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)

            tables = await page.query_selector_all("table")
            rates = []

            for table in tables:
                rows = await table.query_selector_all("tr")
                for row in rows[1:]:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 2:
                        continue
                    texts = [(await c.inner_text()).strip() for c in cells]
                    parsed = _parse_commission_row(texts)
                    rates.extend(parsed)

            return rates if rates else _fallback_commission_rates()

        finally:
            await browser.close()


def _parse_full_shipping_row(cells: list[str]) -> dict | None:
    """
    Tenta extrair uma faixa de frete Full de uma linha de tabela.
    Formato esperado: | Faixa de peso | Preço |
    """
    try:
        weight_text = cells[0]
        price_text = cells[-1]

        # Extrai faixa de peso (ex: "0 a 0,3 kg", "0,3 a 0,7 kg", "acima de 20 kg")
        weight_min, weight_max = _parse_weight_range(weight_text)
        price = _parse_currency(price_text)

        if price is None or weight_max is None:
            return None

        return {
            "logistics": "full",
            "weight_min_kg": weight_min,
            "weight_max_kg": weight_max,
            "price_min": None,
            "price_max": None,
            "rate": price,
        }
    except Exception:
        return None


def _parse_me_shipping_row(cells: list[str]) -> dict | None:
    """Extrai faixa de frete Mercado Envios."""
    try:
        weight_text = cells[0]
        price_text = cells[-1]
        weight_min, weight_max = _parse_weight_range(weight_text)
        price = _parse_currency(price_text)
        if price is None or weight_max is None:
            return None
        return {
            "logistics": "mercado_envios",
            "weight_min_kg": weight_min,
            "weight_max_kg": weight_max,
            "price_min": None,
            "price_max": None,
            "rate": price,
        }
    except Exception:
        return None


def _parse_commission_row(cells: list[str]) -> list[dict]:
    """
    Extrai comissão de uma linha da tabela de categorias.
    Retorna duas entradas (classic e premium) por categoria.
    """
    results = []
    try:
        if len(cells) < 2:
            return []

        category_name = cells[0]
        if not category_name or any(
            skip in category_name.lower()
            for skip in ["categoria", "tipo", "comissão", "anúncio"]
        ):
            return []

        # Tenta extrair percentuais da linha
        percentages = []
        for cell in cells[1:]:
            pct = _parse_percentage(cell)
            if pct is not None:
                percentages.append(pct)

        if not percentages:
            return []

        # ML geralmente mostra: Classic | Premium
        classic_rate = percentages[0]
        premium_rate = percentages[1] if len(percentages) > 1 else percentages[0]

        # Usa o nome da categoria como ID simplificado (será refinado)
        category_id = _category_name_to_id(category_name)

        results.append({
            "category_id": category_id,
            "category_name": category_name.strip(),
            "ad_type": "classic",
            "commission_rate": classic_rate,
        })
        results.append({
            "category_id": category_id,
            "category_name": category_name.strip(),
            "ad_type": "premium",
            "commission_rate": premium_rate,
        })

    except Exception as exc:
        logger.debug(f"Erro ao parsear linha de comissão: {exc}")

    return results


# ─── Helpers de parsing ──────────────────────────────────────────────────────

def _parse_weight_range(text: str) -> tuple[float, float]:
    """Converte '0,3 a 0,7 kg' → (0.3, 0.7). 'acima de 20 kg' → (20.0, 999.0)."""
    text = text.lower().replace(",", ".")

    if "acima" in text or "mais" in text:
        match = re.search(r"([\d.]+)", text)
        if match:
            val = float(match.group(1))
            return val, 999.0

    numbers = re.findall(r"[\d.]+", text)
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    if len(numbers) == 1:
        return 0.0, float(numbers[0])

    return 0.0, 0.0


def _parse_currency(text: str) -> float | None:
    """Converte 'R$ 12,90' → 12.90."""
    try:
        clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        match = re.search(r"[\d.]+", clean)
        return float(match.group()) if match else None
    except Exception:
        return None


def _parse_percentage(text: str) -> float | None:
    """Converte '14%' → 14.0."""
    try:
        match = re.search(r"([\d,]+)%", text)
        if match:
            return float(match.group(1).replace(",", "."))
    except Exception:
        pass
    return None


def _category_name_to_id(name: str) -> str:
    """Gera um ID simplificado a partir do nome da categoria."""
    return "MLB_" + re.sub(r"[^a-zA-Z0-9]", "_", name.strip().upper())[:30]


# ─── Fallbacks (valores de referência de jun/2025) ───────────────────────────
# Usados quando o scraping falha. Atualizar manualmente se necessário.

def _fallback_full_rates() -> list[dict]:
    """Tabela de frete Full — referência jun/2025."""
    return [
        {"logistics": "full", "weight_min_kg": 0.0,  "weight_max_kg": 0.3,   "price_min": None, "price_max": None, "rate": 5.99},
        {"logistics": "full", "weight_min_kg": 0.3,  "weight_max_kg": 0.7,   "price_min": None, "price_max": None, "rate": 8.49},
        {"logistics": "full", "weight_min_kg": 0.7,  "weight_max_kg": 1.0,   "price_min": None, "price_max": None, "rate": 10.99},
        {"logistics": "full", "weight_min_kg": 1.0,  "weight_max_kg": 2.0,   "price_min": None, "price_max": None, "rate": 13.99},
        {"logistics": "full", "weight_min_kg": 2.0,  "weight_max_kg": 5.0,   "price_min": None, "price_max": None, "rate": 18.99},
        {"logistics": "full", "weight_min_kg": 5.0,  "weight_max_kg": 10.0,  "price_min": None, "price_max": None, "rate": 26.99},
        {"logistics": "full", "weight_min_kg": 10.0, "weight_max_kg": 15.0,  "price_min": None, "price_max": None, "rate": 36.99},
        {"logistics": "full", "weight_min_kg": 15.0, "weight_max_kg": 20.0,  "price_min": None, "price_max": None, "rate": 46.99},
        {"logistics": "full", "weight_min_kg": 20.0, "weight_max_kg": 999.0, "price_min": None, "price_max": None, "rate": 59.99},
    ]


def _fallback_me_rates() -> list[dict]:
    """Tabela de frete Mercado Envios — referência jun/2025."""
    return [
        {"logistics": "mercado_envios", "weight_min_kg": 0.0,  "weight_max_kg": 0.3,   "price_min": None, "price_max": None, "rate": 9.90},
        {"logistics": "mercado_envios", "weight_min_kg": 0.3,  "weight_max_kg": 0.7,   "price_min": None, "price_max": None, "rate": 12.90},
        {"logistics": "mercado_envios", "weight_min_kg": 0.7,  "weight_max_kg": 1.0,   "price_min": None, "price_max": None, "rate": 15.90},
        {"logistics": "mercado_envios", "weight_min_kg": 1.0,  "weight_max_kg": 2.0,   "price_min": None, "price_max": None, "rate": 19.90},
        {"logistics": "mercado_envios", "weight_min_kg": 2.0,  "weight_max_kg": 5.0,   "price_min": None, "price_max": None, "rate": 27.90},
        {"logistics": "mercado_envios", "weight_min_kg": 5.0,  "weight_max_kg": 10.0,  "price_min": None, "price_max": None, "rate": 39.90},
        {"logistics": "mercado_envios", "weight_min_kg": 10.0, "weight_max_kg": 20.0,  "price_min": None, "price_max": None, "rate": 59.90},
        {"logistics": "mercado_envios", "weight_min_kg": 20.0, "weight_max_kg": 999.0, "price_min": None, "price_max": None, "rate": 89.90},
    ]


def _fallback_commission_rates() -> list[dict]:
    """
    Comissões por categoria — referência jun/2025.
    Fonte: https://www.mercadolivre.com.br/ajuda/custos-de-venda_1338
    """
    categories = [
        ("MLB174391", "Acessórios para Veículos",      11.0, 16.0),
        ("MLB1000",   "Antiguidades e Coleções",        14.0, 16.0),
        ("MLB1144",   "Bebês",                          14.0, 16.0),
        ("MLB1246",   "Beleza e Cuidado Pessoal",       14.0, 16.0),
        ("MLB1500",   "Calçados, Roupas e Bolsas",      14.0, 16.0),
        ("MLB1039",   "Câmeras e Acessórios",           14.0, 16.0),
        ("MLB1051",   "Casa, Móveis e Decoração",       14.0, 16.0),
        ("MLB1648",   "Eletrônicos, Áudio e Vídeo",     14.0, 16.0),
        ("MLB218519", "Esportes e Fitness",              14.0, 16.0),
        ("MLB1196",   "Ferramentas e Construção",        14.0, 16.0),
        ("MLB1168",   "Games",                          14.0, 16.0),
        ("MLB3937",   "Iluminação e Elétrica",           14.0, 16.0),
        ("MLB1459",   "Imóveis",                         5.0,  5.0),
        ("MLB1743",   "Indústria e Comércio",            14.0, 16.0),
        ("MLB1499",   "Informática",                     14.0, 16.0),
        ("MLB1071",   "Instrumentos Musicais",           14.0, 16.0),
        ("MLB4655",   "Jardim e Animais",                14.0, 16.0),
        ("MLB2197",   "Livros, Revistas e Comics",       14.0, 16.0),
        ("MLB1182",   "Saúde",                           14.0, 16.0),
        ("MLB1953",   "Serviços",                        17.0, 17.0),
        ("MLB1540",   "Telefonia e Celulares",            14.0, 16.0),
        ("MLB1574",   "Veículos e Embarcações",           3.0,  3.0),
        ("MLB1132",   "Brinquedos e Hobbies",            14.0, 16.0),
        ("MLB2531",   "Alimentos e Bebidas",              14.0, 16.0),
        ("MLB3913",   "Eletrodomésticos",                 14.0, 16.0),
    ]

    rates = []
    for cat_id, cat_name, classic_rate, premium_rate in categories:
        rates.append({
            "category_id": cat_id,
            "category_name": cat_name,
            "ad_type": "classic",
            "commission_rate": classic_rate,
        })
        rates.append({
            "category_id": cat_id,
            "category_name": cat_name,
            "ad_type": "premium",
            "commission_rate": premium_rate,
        })

    return rates
