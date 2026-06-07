"""
Motor de cálculo de margens.
Consulta as tabelas de frete e comissão salvas no banco (atualizadas diariamente)
e calcula a margem para dois cenários: ranqueamento e pós-ranqueamento.
"""
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MLShippingRate, MLCommissionRate, Analysis, Product, Listing

logger = logging.getLogger(__name__)


async def calculate_margin(
    db: AsyncSession,
    product: Product,
    logistics_mode: str,  # "full" | "mercado_envios"
    ad_type: str,         # "classic" | "premium"
    category_id: str,
    tax_rate: float,      # percentual ex: 4.0
) -> Analysis:
    """
    Calcula margem para a combinação escolhida e salva no banco.
    Retorna o objeto Analysis criado.
    """

    # 1. Busca anúncios selecionados pelo usuário
    result = await db.execute(
        select(Listing).where(
            and_(
                Listing.product_id == product.id,
                Listing.selected_by_user == True,
            )
        )
    )
    selected = result.scalars().all()

    if not selected:
        raise ValueError("Nenhum anúncio selecionado para calcular a margem.")

    prices = [float(l.price) for l in selected]
    suggested_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    # 2. Preço para o cenário de ranqueamento (menor preço geral na busca)
    all_listings_result = await db.execute(
        select(Listing.price).where(Listing.product_id == product.id)
    )
    all_prices = [float(p) for p in all_listings_result.scalars().all()]
    ranking_price = min(all_prices) if all_prices else suggested_price

    # 3. Comissão da categoria
    commission_result = await db.execute(
        select(MLCommissionRate).where(
            and_(
                MLCommissionRate.category_id == category_id,
                MLCommissionRate.ad_type == ad_type,
            )
        )
    )
    commission_row = commission_result.scalar_one_or_none()
    commission_rate = float(commission_row.commission_rate) / 100 if commission_row else 0.14

    # 4. Custo de frete para o cenário pós-ranqueamento (preço sugerido)
    shipping_cost = await _get_shipping_cost(
        db=db,
        logistics=logistics_mode,
        weight_kg=float(product.weight_kg or 0.5),
        sale_price=suggested_price,
    )

    # 5. Calcula margens
    cost_price = float(product.cost_price)

    def calc_margin(sale_price: float) -> float:
        commission = sale_price * commission_rate
        tax = sale_price * (tax_rate / 100)
        net = sale_price - commission - shipping_cost - tax - cost_price
        return (net / sale_price) * 100

    margin_post = calc_margin(suggested_price)
    margin_rank = calc_margin(ranking_price)

    # 6. Veredito
    verdict = "approved" if margin_post >= 15.0 and margin_rank >= 0.0 else "rejected"
    rejection_reason = None
    if verdict == "rejected":
        reasons = []
        if margin_post < 15.0:
            reasons.append(f"margem pós-ranqueamento {margin_post:.1f}% < 15%")
        if margin_rank < 0.0:
            reasons.append(f"prejuízo no ranqueamento ({margin_rank:.1f}%)")
        rejection_reason = " | ".join(reasons)

    # 7. Salva a análise
    analysis = Analysis(
        product_id=product.id,
        logistics_mode=logistics_mode,
        ad_type=ad_type,
        suggested_price=round(suggested_price, 2),
        min_competitor_price=round(min_price, 2),
        max_competitor_price=round(max_price, 2),
        ml_commission_rate=round(commission_rate * 100, 2),
        shipping_cost=round(shipping_cost, 2),
        tax_cost=round(suggested_price * (tax_rate / 100), 2),
        total_cost=round(
            cost_price + shipping_cost + suggested_price * (commission_rate + tax_rate / 100),
            2,
        ),
        margin_ranking=round(margin_rank, 2),
        margin_post_ranking=round(margin_post, 2),
        verdict=verdict,
        rejection_reason=rejection_reason,
    )

    db.add(analysis)
    product.status = "done"
    await db.commit()
    await db.refresh(analysis)

    logger.info(
        f"[{product.catalog_name}] {logistics_mode.upper()} + {ad_type} → "
        f"pós: {margin_post:.1f}% | rank: {margin_rank:.1f}% | {verdict.upper()}"
    )

    return analysis


async def _get_shipping_cost(
    db: AsyncSession,
    logistics: str,
    weight_kg: float,
    sale_price: float,
) -> float:
    """Consulta a faixa de frete correta na tabela do banco."""
    result = await db.execute(
        select(MLShippingRate).where(
            and_(
                MLShippingRate.logistics == logistics,
                MLShippingRate.weight_min_kg <= weight_kg,
                MLShippingRate.weight_max_kg >= weight_kg,
            )
        ).order_by(MLShippingRate.weight_min_kg.asc())
        .limit(1)
    )
    rate = result.scalar_one_or_none()

    if rate:
        return float(rate.rate)

    # Fallback: frete não encontrado na tabela — usa estimativa conservadora
    logger.warning(
        f"Frete não encontrado para {logistics} / {weight_kg}kg. Usando fallback."
    )
    return weight_kg * 8.0  # R$8/kg como estimativa de segurança
