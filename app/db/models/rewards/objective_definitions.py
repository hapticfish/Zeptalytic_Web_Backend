from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class ObjectiveDefinition(Base):
    __tablename__ = "objective_definitions"
    __table_args__ = (
        Index("ix_objective_definitions_sort_group_sort_order", "sort_group", "sort_order"),
        Index("ix_objective_definitions_scope_type", "scope_type"),
        Index("uq_objective_definitions_objective_code", "objective_code", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    objective_code: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objective_type: Mapped[str] = mapped_column(String(64), nullable=False)
    is_repeatable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    repeat_group_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    tier_gate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subscription_gate_product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subscription_gate_plan_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_milestone_objective: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    sort_group: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    objective_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
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

    account_progress_entries: Mapped[list["AccountObjectiveProgress"]] = relationship(
        back_populates="objective_definition",
        cascade="all, delete-orphan",
    )
    objective_reward_links: Mapped[list["ObjectiveRewardLink"]] = relationship(
        back_populates="objective_definition",
        cascade="all, delete-orphan",
    )
    reward_grants: Mapped[list["RewardGrant"]] = relationship(
        back_populates="source_objective_definition"
    )
    account_badges: Mapped[list["AccountBadge"]] = relationship(
        back_populates="source_objective_definition"
    )
    reward_events: Mapped[list["RewardEvent"]] = relationship(
        back_populates="objective_definition"
    )
    linked_reward_milestones: Mapped[list["RewardMilestone"]] = relationship(
        back_populates="linked_objective_definition"
    )
