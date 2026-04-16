from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RewardAccount(Base):
    __tablename__ = "reward_accounts"

    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_tier: Mapped[str] = mapped_column(String(32), nullable=False, server_default="BRONZE")
    current_tier_progress_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    next_milestone_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    last_recomputed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped["Account"] = relationship(back_populates="reward_account")

