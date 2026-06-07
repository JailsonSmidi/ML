"""
Estimativa de visitas nos últimos 7 dias com base em dados públicos.
Mesma metodologia usada por ferramentas como Seller Vision e Hunter Spy:
sem acesso à API de visitas de terceiros, usamos heurísticas baseadas em
posição na busca, tag de vendas e dias no ar.
"""


# Peso de visitação estimada por posição na página de busca
# Queda exponencial — posição 1 tem muito mais tráfego que posição 20
POSITION_VISIT_WEIGHTS = {
    1: 1.00,
    2: 0.72,
    3: 0.58,
    4: 0.46,
    5: 0.38,
    6: 0.30,
    7: 0.24,
    8: 0.20,
    9: 0.17,
    10: 0.14,
    11: 0.12,
    12: 0.10,
    13: 0.09,
    14: 0.08,
    15: 0.07,
    16: 0.06,
    17: 0.055,
    18: 0.05,
    19: 0.045,
    20: 0.04,
}

# Taxa de conversão média em marketplaces brasileiros (~1–3%)
# Usamos 1.5% como base conservadora para estimar: visitas = vendas / conversão
BASE_CONVERSION_RATE = 0.015


def estimate_visits(
    search_position: int,
    sales_tag: int | None,
    listing_age_days: int,
) -> int:
    """
    Retorna uma estimativa de visitas nos últimos 7 dias.

    Combina dois sinais:
    1. Visitas implícitas pelas vendas (sales_tag / dias * 7 / conversão)
    2. Ajuste pela posição na busca (anúncios mais bem posicionados têm mais tráfego)

    O resultado é uma estimativa — não um dado exato da API do ML.
    """
    if not sales_tag or listing_age_days < 1:
        # Sem dados de vendas, usa só a posição como proxy mínimo
        position_weight = POSITION_VISIT_WEIGHTS.get(
            min(search_position, 20), 0.03
        )
        # Assume que o anúncio na posição 1 tem ~500 visitas/semana como base de mercado
        return int(500 * position_weight)

    # Vendas nos últimos 7 dias (estimativa proporcional)
    age_days = max(listing_age_days, 1)
    sales_per_day = sales_tag / age_days
    sales_last_7d = sales_per_day * 7

    # Visitas estimadas: vendas / taxa de conversão
    visits_from_sales = sales_last_7d / BASE_CONVERSION_RATE

    # Fator de ajuste pela posição
    position_weight = POSITION_VISIT_WEIGHTS.get(
        min(search_position, 20), 0.03
    )
    position_multiplier = 0.5 + (position_weight * 2)
    # Varia de ~0.56 (posição 20) a 2.5 (posição 1)
    # Evita que anúncios mal posicionados com muitas vendas acumuladas
    # (produto antigo, mas caído de posição) sejam superestimados

    estimated = int(visits_from_sales * position_multiplier)
    return max(estimated, 0)
