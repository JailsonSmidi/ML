import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE")
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True
    )

    # Dados extraídos do PDF
    catalog_name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_price: Mapped[float] = mapped_column(Numeric(10, 2))
    units_per_box: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Estimativas da IA
    weight_kg: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    dimensions_cm: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {"length": 30.0, "width": 20.0, "height": 10.0}

    # Termos de busca
    search_terms: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # ["ring light", "ringue lite", "luz de led circular"]
    best_search_term: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Controle de fluxo
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
        # pending | scraping | awaiting_selection | analysing | done | error
    )
    batch_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="products")  # noqa: F821
    batch: Mapped["Batch"] = relationship(back_populates="products")  # noqa: F821
    listings: Mapped[list["Listing"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
