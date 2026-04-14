from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT
from app.db.models.accounts import Account


class EntitlementSummary(Base):
    __tablename__ = "entitlement_summaries"
    __table_args__ = (
        Index("ix_entitlement_summaries_account_id", "account_id"),
        Index("ix_entitlement_summaries_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the normalized entitlement-status vocabulary in the Pay integration contract/spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entitlement_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="entitlement_summaries")
