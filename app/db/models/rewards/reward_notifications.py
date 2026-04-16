from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class RewardNotification(Base):
    __tablename__ = "reward_notifications"
    __table_args__ = (
        Index("ix_reward_notifications_account_id", "account_id"),
        Index("ix_reward_notifications_status", "status"),
        Index("ix_reward_notifications_sequence_order", "sequence_order"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    objective_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("objective_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    reward_grant_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("reward_grants.id", ondelete="SET NULL"),
        nullable=True,
    )
    badge_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("badge_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    reward_event_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("reward_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    notification_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    account: Mapped["Account"] = relationship(back_populates="reward_notifications")
    objective_definition: Mapped["ObjectiveDefinition | None"] = relationship(
        back_populates="reward_notifications"
    )
    reward_grant: Mapped["RewardGrant | None"] = relationship(
        back_populates="reward_notifications"
    )
    badge_definition: Mapped["BadgeDefinition | None"] = relationship(
        back_populates="reward_notifications"
    )
    reward_event: Mapped["RewardEvent | None"] = relationship(
        back_populates="reward_notifications"
    )
