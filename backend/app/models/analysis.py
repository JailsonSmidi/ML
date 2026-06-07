import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )

    # Combinação simulada
    logistics_mode: Mapped[str] = mapped_column(String(30))
    # full | mercado_envios
    ad_type: Mapped[str] = mapped_column(String(20))
    # classic | premium

    # Preços de referência
    suggested_price: Mapped[float] = mapped_column(Numeric(10, 2))
    min_competitor_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    max_competitor_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Custos aplicados
    ml_commission_rate: Mapped[float] = mapped_column(Numeric(5, 2))
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2))
    tax_cost: Mapped[float] = mapped_column(Numeric(10, 2))
    total_cost: Mapped[float] = mapped_column(Numeric(10, 2))

    # Resultados
    margin_ranking: Mapped[float] = mapped_column(Numeric(5, 2))
    margin_post_ranking: Mapped[float] = mapped_column(Numeric(5, 2))
    verdict: Mapped[str] = mapped_column(String(20))
    # approved | rejected
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="analyses")  # noqa: F821


class MLShippingRate(Base):
    """Tabela de fretes Full e Mercado Envios — sincronizada diariamente do site do ML."""

    __tablename__ = "ml_shipping_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    logistics: Mapped[str] = mapped_column(String(30))
    # full | mercado_envios
    weight_min_kg: Mapped[float] = mapped_column(Numeric(8, 3))
    weight_max_kg: Mapped[float] = mapped_column(Numeric(8, 3))
    price_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    rate: Mapped[float] = mapped_column(Numeric(10, 2))
    # valor em R$ do frete para essa faixa
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MLCommissionRate(Base):
    """Comissões por categoria e tipo de anúncio — sincronizadas diariamente."""

    __tablename__ = "ml_commission_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[str] = mapped_column(String(50))
    # ex: MLB1648 (Eletrônicos)
    category_name: Mapped[str] = mapped_column(String(255))
    ad_type: Mapped[str] = mapped_column(String(20))
    # classic | premium
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2))
    # percentual ex: 14.00
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MLTableSyncLog(Base):
    """Histórico de cada sincronização das tabelas do ML."""

    __tablename__ = "ml_table_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(50))
    # ml_shipping_rates | ml_commission_rates
    changes_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    changes_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # [{"field": "rate", "category": "MLB1648", "old": 14.0, "new": 16.0}]
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Notification(Base):
    """Notificações exibidas no dashboard e enviadas por email."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[str] = mapped_column(String(50))
    # table_sync_change | scrape_error | batch_done
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
