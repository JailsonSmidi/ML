import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )

    # Dados do ML
    ml_item_id: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Classificação do anúncio
    listing_type: Mapped[str] = mapped_column(String(20))
    # catalog | organic
    logistics: Mapped[str] = mapped_column(String(30))
    # full | mercado_envios
    ad_type: Mapped[str] = mapped_column(String(20))
    # classic | premium

    # Métricas coletadas
    sales_tag: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # número extraído de "+500 vendidos" → 500
    listing_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Métricas calculadas
    estimated_visits_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sales_per_day_est: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )

    # Seleção pelo usuário
    selected_by_user: Mapped[bool] = mapped_column(Boolean, default=False)

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="listings")  # noqa: F821
