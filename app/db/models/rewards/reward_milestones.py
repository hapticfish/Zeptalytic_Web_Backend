from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RewardMilestone(Base):
    __tablename__ = "reward_milestones"
    __table_args__ = (
        Index("ix_reward_milestones_sort_order", "sort_order"),
        Index("uq_reward_milestones_milestone_points", "milestone_points", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    milestone_points: Mapped[int] = mapped_column(Integer, nullable=False)
    tier_code: Mapped[str] = mapped_column(String(32), nullable=False)
    is_tier_boundary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    linked_objective_definition_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
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
