from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class RewardEvent(Base):
    __tablename__ = "reward_events"
    __table_args__ = (
        Index("ix_reward_events_account_id", "account_id"),
        Index("ix_reward_events_created_at", "created_at"),
        Index("ix_reward_events_reversed_event_id", "reversed_event_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    objective_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("objective_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    reward_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("reward_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    badge_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("badge_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_reversal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    reversed_event_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("reward_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    event_metadata: Mapped[dict[str, object]] = mapped_column(
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

    account: Mapped["Account"] = relationship(back_populates="reward_events")
    objective_definition: Mapped["ObjectiveDefinition | None"] = relationship(
        back_populates="reward_events"
    )
    reward_definition: Mapped["RewardDefinition | None"] = relationship(
        back_populates="reward_events"
    )
    badge_definition: Mapped["BadgeDefinition | None"] = relationship(
        back_populates="reward_events"
    )
    reward_grants: Mapped[list["RewardGrant"]] = relationship(
        back_populates="source_reward_event"
    )
    account_badges: Mapped[list["AccountBadge"]] = relationship(
        back_populates="source_reward_event"
    )
    reversed_event: Mapped["RewardEvent | None"] = relationship(
        remote_side="RewardEvent.id",
        foreign_keys=[reversed_event_id],
    )
