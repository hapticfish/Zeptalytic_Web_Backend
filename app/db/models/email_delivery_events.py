from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class EmailDeliveryEvent(Base):
    __tablename__ = "email_delivery_events"
    __table_args__ = (
        Index("ix_email_delivery_events_provider_message_id", "provider_message_id"),
        Index("ix_email_delivery_events_provider_event_id", "provider_event_id"),
        Index("ix_email_delivery_events_email", "email"),
        Index("ix_email_delivery_events_event_type", "event_type"),
        Index("ix_email_delivery_events_template_id", "template_id"),
        Index("ix_email_delivery_events_event_timestamp", "event_timestamp"),
        Index("ix_email_delivery_events_created_at", "created_at"),
        Index("ux_email_delivery_events_dedupe_key", "dedupe_key", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="brevo",
        server_default=text("'brevo'"),
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
