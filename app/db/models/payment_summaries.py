from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account


class PaymentSummary(Base):
    __tablename__ = "payment_summaries"
    __table_args__ = (
        Index("ix_payment_summaries_account_id", "account_id"),
        Index("ix_payment_summaries_product_code", "product_code"),
        Index("ix_payment_summaries_payment_rail", "payment_rail"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # TODO(john): Lock the payment-rail vocabulary in the Pay integration contract/spec.
    payment_rail: Mapped[str] = mapped_column(String(32), nullable=False)
    # TODO(john): Lock the normalized payment-status vocabulary in the Pay integration contract/spec.
    normalized_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_status_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account] = relationship(back_populates="payment_summaries")
