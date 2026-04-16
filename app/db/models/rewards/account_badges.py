from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class AccountBadge(Base):
    __tablename__ = "account_badges"
    __table_args__ = (
        Index("ix_account_badges_account_id", "account_id"),
        Index("ix_account_badges_badge_definition_id", "badge_definition_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    badge_definition_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("badge_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_objective_definition_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("objective_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_reward_event_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("reward_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    badge_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    account: Mapped["Account"] = relationship(back_populates="account_badges")
    badge_definition: Mapped["BadgeDefinition"] = relationship(back_populates="account_badges")
    source_objective_definition: Mapped["ObjectiveDefinition | None"] = relationship(
        back_populates="account_badges"
    )
    source_reward_event: Mapped["RewardEvent | None"] = relationship(
        back_populates="account_badges"
    )
