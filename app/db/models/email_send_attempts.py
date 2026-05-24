from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._json import JSON_VARIANT


class EmailSendAttempt(Base):
    __tablename__ = "email_send_attempts"
    __table_args__ = (
        Index("ix_email_send_attempts_account_id", "account_id"),
        Index("ix_email_send_attempts_to_email", "to_email"),
        Index("ix_email_send_attempts_template_key", "template_key"),
        Index("ix_email_send_attempts_status", "status"),
        Index("ix_email_send_attempts_provider_message_id", "provider_message_id"),
        Index("ix_email_send_attempts_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_email: Mapped[str] = mapped_column(String(320), nullable=False)
    from_email: Mapped[str] = mapped_column(String(320), nullable=False)
    from_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reply_to_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="brevo",
        server_default=text("'brevo'"),
    )
    provider_template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
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
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
