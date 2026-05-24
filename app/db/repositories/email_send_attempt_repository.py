from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.email_send_attempts import EmailSendAttempt


FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "api_key",
        "brevo_api_key",
        "email_body",
        "password_reset_token",
        "raw_password_reset_token",
        "raw_verification_token",
        "rendered_body",
        "rendered_email_body",
        "reset_token",
        "reset_url",
        "token",
        "verification_token",
        "verification_url",
        "webhook_secret",
    }
)

_DROP_METADATA_VALUE = object()


@dataclass(slots=True)
class EmailSendAttemptRecord:
    attempt_id: UUID
    account_id: UUID | None
    to_email: str
    from_email: str
    from_name: str | None
    reply_to_email: str | None
    template_key: str
    provider: str
    provider_template_id: int | None
    provider_message_id: str | None
    status: str
    failure_code: str | None
    failure_message: str | None
    metadata: dict[str, Any]
    created_at: datetime
    sent_at: datetime | None
    failed_at: datetime | None


class EmailSendAttemptRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def create_send_attempt(
        self,
        *,
        account_id: UUID | None,
        to_email: str,
        from_email: str,
        from_name: str | None,
        reply_to_email: str | None,
        template_key: str,
        provider_template_id: int | None,
        status: str,
        provider: str = "brevo",
        metadata: dict[str, Any] | None = None,
    ) -> EmailSendAttemptRecord:
        attempt = EmailSendAttempt(
            account_id=account_id,
            to_email=to_email,
            from_email=from_email,
            from_name=from_name,
            reply_to_email=reply_to_email,
            template_key=template_key,
            provider=provider,
            provider_template_id=provider_template_id,
            status=status,
            attempt_metadata=sanitize_email_send_attempt_metadata(metadata),
        )
        self._db.add(attempt)
        self._db.flush()
        return self._to_record(attempt)

    def mark_sent(
        self,
        attempt_id: UUID,
        *,
        provider_message_id: str | None,
        sent_at: datetime | None = None,
    ) -> EmailSendAttemptRecord | None:
        attempt = self._db.get(EmailSendAttempt, attempt_id)
        if attempt is None:
            return None

        attempt.status = "sent"
        attempt.provider_message_id = provider_message_id
        attempt.sent_at = sent_at or datetime.now(UTC)
        attempt.failed_at = None
        attempt.failure_code = None
        attempt.failure_message = None
        self._db.flush()
        return self._to_record(attempt)

    def mark_failed(
        self,
        attempt_id: UUID,
        *,
        failure_code: str,
        failure_message: str | None,
        failed_at: datetime | None = None,
    ) -> EmailSendAttemptRecord | None:
        attempt = self._db.get(EmailSendAttempt, attempt_id)
        if attempt is None:
            return None

        attempt.status = "failed"
        attempt.failure_code = failure_code
        attempt.failure_message = failure_message
        attempt.failed_at = failed_at or datetime.now(UTC)
        self._db.flush()
        return self._to_record(attempt)

    def mark_skipped(
        self,
        attempt_id: UUID,
        *,
        failure_code: str | None = None,
        failure_message: str | None = None,
    ) -> EmailSendAttemptRecord | None:
        attempt = self._db.get(EmailSendAttempt, attempt_id)
        if attempt is None:
            return None

        attempt.status = "skipped"
        attempt.failure_code = failure_code
        attempt.failure_message = failure_message
        attempt.sent_at = None
        attempt.failed_at = None
        self._db.flush()
        return self._to_record(attempt)

    def get_by_id(self, attempt_id: UUID) -> EmailSendAttemptRecord | None:
        attempt = self._db.get(EmailSendAttempt, attempt_id)
        if attempt is None:
            return None
        return self._to_record(attempt)

    def list_for_account(self, account_id: UUID) -> list[EmailSendAttemptRecord]:
        attempts = self._db.scalars(
            select(EmailSendAttempt)
            .where(EmailSendAttempt.account_id == account_id)
            .order_by(EmailSendAttempt.created_at.desc(), EmailSendAttempt.id.desc())
        ).all()
        return [self._to_record(attempt) for attempt in attempts]

    @staticmethod
    def _to_record(attempt: EmailSendAttempt) -> EmailSendAttemptRecord:
        return EmailSendAttemptRecord(
            attempt_id=attempt.id,
            account_id=attempt.account_id,
            to_email=attempt.to_email,
            from_email=attempt.from_email,
            from_name=attempt.from_name,
            reply_to_email=attempt.reply_to_email,
            template_key=attempt.template_key,
            provider=attempt.provider,
            provider_template_id=attempt.provider_template_id,
            provider_message_id=attempt.provider_message_id,
            status=attempt.status,
            failure_code=attempt.failure_code,
            failure_message=attempt.failure_message,
            metadata=dict(attempt.attempt_metadata),
            created_at=attempt.created_at,
            sent_at=attempt.sent_at,
            failed_at=attempt.failed_at,
        )


def sanitize_email_send_attempt_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    sanitized: dict[str, Any] = {}
    for key, item in value.items():
        if key.casefold() in FORBIDDEN_METADATA_KEYS:
            continue

        sanitized_item = _sanitize_metadata_value(item)
        if sanitized_item is _DROP_METADATA_VALUE:
            continue
        sanitized[key] = sanitized_item

    return sanitized


def _sanitize_metadata_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_email_send_attempt_metadata(value)
    if isinstance(value, list):
        sanitized_items = []
        for item in value:
            sanitized_item = _sanitize_metadata_value(item)
            if sanitized_item is _DROP_METADATA_VALUE:
                continue
            sanitized_items.append(sanitized_item)
        return sanitized_items
    if isinstance(value, str):
        lowered_value = value.casefold()
        if lowered_value.startswith("http") and "token=" in lowered_value:
            return _DROP_METADATA_VALUE
        return value
    return value
