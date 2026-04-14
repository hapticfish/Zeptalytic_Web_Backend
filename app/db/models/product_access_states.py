from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account


class ProductAccessState(Base):
    __tablename__ = "product_access_states"
    __table_args__ = (
        Index("ix_product_access_states_account_id", "account_id"),
        Index("ix_product_access_states_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the launcher access-state vocabulary in the dashboard/launcher spec.
    access_state: Mapped[str] = mapped_column(String(32), nullable=False)
    launch_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    disabled_reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    external_account_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account] = relationship(back_populates="product_access_states")
