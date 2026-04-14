from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account


class PaymentMethodSummary(Base):
    __tablename__ = "payment_method_summaries"
    __table_args__ = (
        Index("ix_payment_method_summaries_account_id", "account_id"),
        Index(
            "uq_payment_method_summaries_provider_method",
            "provider",
            "provider_payment_method_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_payment_method_id: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(32), nullable=False)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    exp_month: Mapped[int] = mapped_column(Integer, nullable=False)
    exp_year: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    # TODO(john): Lock the payment-method summary status vocabulary in the billing spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="payment_method_summaries")
