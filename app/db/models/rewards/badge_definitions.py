from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class BadgeDefinition(Base):
    __tablename__ = "badge_definitions"
    __table_args__ = (
        Index("ix_badge_definitions_display_name", "display_name"),
        Index("uq_badge_definitions_badge_code", "badge_code", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    badge_code: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    icon_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_revocable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    badge_metadata: Mapped[dict[str, object]] = mapped_column(
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

    account_badges: Mapped[list["AccountBadge"]] = relationship(
        back_populates="badge_definition",
        cascade="all, delete-orphan",
    )
    reward_notifications: Mapped[list["RewardNotification"]] = relationship(
        back_populates="badge_definition"
    )
    reward_events: Mapped[list["RewardEvent"]] = relationship(back_populates="badge_definition")
