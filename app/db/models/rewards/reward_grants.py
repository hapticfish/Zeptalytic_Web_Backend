from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class RewardGrant(Base):
    __tablename__ = "reward_grants"
    __table_args__ = (
        Index("ix_reward_grants_account_id", "account_id"),
        Index("ix_reward_grants_reward_definition_id", "reward_definition_id"),
        Index("ix_reward_grants_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    reward_definition_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("reward_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grant_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    account: Mapped["Account"] = relationship(back_populates="reward_grants")
    reward_definition: Mapped["RewardDefinition"] = relationship(back_populates="reward_grants")
    source_objective_definition: Mapped["ObjectiveDefinition | None"] = relationship(
        back_populates="reward_grants"
    )
    source_reward_event: Mapped["RewardEvent | None"] = relationship(
        back_populates="reward_grants"
    )
    reward_notifications: Mapped[list["RewardNotification"]] = relationship(
        back_populates="reward_grant"
    )
