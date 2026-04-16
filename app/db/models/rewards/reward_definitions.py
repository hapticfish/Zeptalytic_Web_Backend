from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class RewardDefinition(Base):
    __tablename__ = "reward_definitions"
    __table_args__ = (
        Index("ix_reward_definitions_reward_type", "reward_type"),
        Index("uq_reward_definitions_reward_code", "reward_code", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    reward_code: Mapped[str] = mapped_column(String(128), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_repeatable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    is_revocable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    grant_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    reward_metadata: Mapped[dict[str, object]] = mapped_column(
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

    objective_reward_links: Mapped[list["ObjectiveRewardLink"]] = relationship(
        back_populates="reward_definition",
        cascade="all, delete-orphan",
    )
    reward_grants: Mapped[list["RewardGrant"]] = relationship(
        back_populates="reward_definition",
        cascade="all, delete-orphan",
    )
    reward_events: Mapped[list["RewardEvent"]] = relationship(
        back_populates="reward_definition"
    )

