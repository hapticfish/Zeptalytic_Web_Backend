from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account


class SubscriptionSummary(Base):
    __tablename__ = "subscription_summaries"
    __table_args__ = (
        Index("ix_subscription_summaries_account_id", "account_id"),
        Index("ix_subscription_summaries_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the billing-interval vocabulary in the Pay integration contract/spec.
    billing_interval: Mapped[str] = mapped_column(String(32), nullable=False)
    # TODO(john): Lock the normalized subscription-status vocabulary in the Pay integration contract/spec.
    normalized_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_status_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    current_period_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="subscription_summaries")
