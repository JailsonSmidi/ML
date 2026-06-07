"""
Term Validator — seleciona o melhor termo de busca para um produto no ML.

Lógica de pontuação (igual ao que o Seller Vision faz internamente):
1. Volume de resultados retornados pela busca
2. Percentual de títulos que contêm o termo de busca
3. Coerência semântica (avaliada pelo Claude com base nos títulos retornados)

O termo com maior pontuação combinada é selecionado automaticamente.
Se apenas um termo for candidato, ele é aceito sem validação.
"""

import logging
import asyncio
import re
from anthropic import AsyncAnthropic
from app.services.scraper import fetch_search_results_count
from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

# Pesos para o score final
WEIGHT_VOLUME = 0.5       # volume de resultados é o sinal mais forte
WEIGHT_TITLE_MATCH = 0.3  # % de títulos contendo o termo
WEIGHT_COHERENCE = 0.2    # avaliação semântica do Claude


async def validate_search_terms(
    catalog_name: str,
    description: str | None,
    candidates: list[str],
) -> tuple[str, list[str]]:
    """
    Avalia os termos candidatos e retorna o melhor + lista completa.

    Returns:
        (best_term, all_terms) — best_term é o vencedor, all_terms é a lista completa
    """
    if not candidates:
        # Sem candidatos — usa o nome do catálogo como fallback
        fallback = catalog_name.lower().strip()
        logger.warning(f"Sem termos candidatos para '{catalog_name}', usando nome do catálogo")
        return fallback, [fallback]

    if len(candidates) == 1:
        return candidates[0], candidates

    logger.info(f"Validando {len(candidates)} termos para '{catalog_name}'")

    # Busca paralela — evita esperar cada termo sequencialmente
    tasks = [_score_term(term, catalog_name) for term in candidates]
    scores = await asyncio.gather(*tasks, return_exceptions=True)

    scored = []
    for term, score in zip(candidates, scores):
        if isinstance(score, Exception):
            logger.warning(f"Erro ao pontuar termo '{term}': {score}")
            scored.append((term, 0.0))
        else:
            scored.append((term, score))
            logger.debug(f"  '{term}' → score {score:.3f}")

    # Ordena pelo score
    scored.sort(key=lambda x: x[1], reverse=True)
    best_term = scored[0][0]

    logger.info(
        f"Melhor termo para '{catalog_name}': '{best_term}' "
        f"(score {scored[0][1]:.3f})"
    )

    return best_term, candidates


async def _score_term(term: str, catalog_name: str) -> float:
    """
    Calcula o score de um termo individualmente.
    Retorna valor entre 0.0 e 1.0.
    """
    try:
        result = await fetch_search_results_count(term)
        total_results = result.get("total_results", 0)
        titles = result.get("sample_titles", [])

        # 1. Score por volume (normalizado — 10k+ resultados = score máximo)
        volume_score = min(total_results / 10_000, 1.0)

        # 2. Score por presença do termo nos títulos
        title_match_score = _calc_title_match(term, titles)

        # 3. Score de coerência semântica via Claude
        coherence_score = await _calc_coherence(
            term=term,
            catalog_name=catalog_name,
            titles=titles[:10],  # amostra dos 10 primeiros títulos
        )

        final_score = (
            volume_score * WEIGHT_VOLUME
            + title_match_score * WEIGHT_TITLE_MATCH
            + coherence_score * WEIGHT_COHERENCE
        )

        return round(final_score, 4)

    except Exception as exc:
        logger.error(f"Erro ao pontuar '{term}': {exc}")
        raise


def _calc_title_match(term: str, titles: list[str]) -> float:
    """
    Percentual de títulos que contêm o termo ou suas palavras principais.
    Ignora palavras curtas (artigos, preposições).
    """
    if not titles:
        return 0.0

    # Palavras significativas do termo (>= 3 chars)
    words = [w for w in term.lower().split() if len(w) >= 3]
    if not words:
        return 0.0

    matches = 0
    for title in titles:
        title_lower = title.lower()
        # Considera match se pelo menos metade das palavras do termo aparecerem
        word_matches = sum(1 for w in words if w in title_lower)
        if word_matches >= max(1, len(words) // 2):
            matches += 1

    return matches / len(titles)


async def _calc_coherence(
    term: str,
    catalog_name: str,
    titles: list[str],
) -> float:
    """
    Usa Claude para avaliar se os títulos dos anúncios correspondem
    ao produto descrito pelo nome do catálogo.
    Retorna float de 0.0 a 1.0.
    """
    if not titles:
        return 0.5  # neutro quando não há títulos para avaliar

    titles_str = "\n".join(f"- {t}" for t in titles)
    prompt = f"""
Avalie se os anúncios abaixo correspondem ao produto descrito.

Produto do catálogo: "{catalog_name}"
Termo de busca usado: "{term}"
Primeiros títulos retornados pela busca:
{titles_str}

Responda APENAS com um número de 0 a 10:
- 0 = nenhum anúncio tem relação com o produto
- 5 = alguns anúncios correspondem, mas há muita divergência
- 10 = a maioria dos anúncios claramente é o mesmo produto

Número:"""

    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",  # modelo rápido e barato para esta tarefa
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Extrai o número da resposta
        match = re.search(r"\d+", raw)
        if match:
            score = int(match.group())
            return min(max(score / 10, 0.0), 1.0)
    except Exception as exc:
        logger.warning(f"Erro na avaliação de coerência: {exc}")

    return 0.5  # fallback neutro em caso de erro
