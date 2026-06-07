import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    supplier_name: Mapped[str] = mapped_column(String(255))
    pdf_filename: Mapped[str] = mapped_column(String(500))
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=4.00)
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
        # pending | processing | awaiting_review | done | error
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    batches: Mapped[list["Batch"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
