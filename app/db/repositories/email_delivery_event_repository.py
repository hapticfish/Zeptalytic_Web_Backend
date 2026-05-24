from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.email_delivery_events import EmailDeliveryEvent


@dataclass(slots=True)
class EmailDeliveryEventRecord:
    event_id: UUID
    provider: str
    event_type: str
    provider_message_id: str | None
    provider_event_id: str | None
    email: str | None
    template_id: int | None
    subject: str | None
    event_timestamp: datetime | None
    dedupe_key: str
    raw_payload: dict[str, object]
    created_at: datetime


@dataclass(slots=True)
class EmailDeliveryEventCreateResult:
    created: bool
    record: EmailDeliveryEventRecord


class EmailDeliveryEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def create_event_if_new(
        self,
        *,
        event_type: str,
        dedupe_key: str,
        raw_payload: dict[str, object],
        provider: str = "brevo",
        provider_message_id: str | None = None,
        provider_event_id: str | None = None,
        email: str | None = None,
        template_id: int | None = None,
        subject: str | None = None,
        event_timestamp: datetime | None = None,
    ) -> EmailDeliveryEventCreateResult:
        existing = self.get_by_dedupe_key(dedupe_key)
        if existing is not None:
            return EmailDeliveryEventCreateResult(created=False, record=existing)

        event = EmailDeliveryEvent(
            provider=provider,
            event_type=event_type,
            provider_message_id=provider_message_id,
            provider_event_id=provider_event_id,
            email=email,
            template_id=template_id,
            subject=subject,
            event_timestamp=event_timestamp,
            dedupe_key=dedupe_key,
            raw_payload=dict(raw_payload),
        )
        self._db.add(event)
        try:
            self._db.flush()
        except IntegrityError:
            self._db.rollback()
            existing = self.get_by_dedupe_key(dedupe_key)
            if existing is None:
                raise
            return EmailDeliveryEventCreateResult(created=False, record=existing)
        return EmailDeliveryEventCreateResult(created=True, record=self._to_record(event))

    def get_by_dedupe_key(self, dedupe_key: str) -> EmailDeliveryEventRecord | None:
        event = self._db.scalar(
            select(EmailDeliveryEvent).where(EmailDeliveryEvent.dedupe_key == dedupe_key)
        )
        if event is None:
            return None
        return self._to_record(event)

    def list_for_provider_message_id(self, provider_message_id: str) -> list[EmailDeliveryEventRecord]:
        events = self._db.scalars(
            select(EmailDeliveryEvent)
            .where(EmailDeliveryEvent.provider_message_id == provider_message_id)
            .order_by(EmailDeliveryEvent.created_at.desc(), EmailDeliveryEvent.id.desc())
        ).all()
        return [self._to_record(event) for event in events]

    @staticmethod
    def _to_record(event: EmailDeliveryEvent) -> EmailDeliveryEventRecord:
        return EmailDeliveryEventRecord(
            event_id=event.id,
            provider=event.provider,
            event_type=event.event_type,
            provider_message_id=event.provider_message_id,
            provider_event_id=event.provider_event_id,
            email=event.email,
            template_id=event.template_id,
            subject=event.subject,
            event_timestamp=event.event_timestamp,
            dedupe_key=event.dedupe_key,
            raw_payload=dict(event.raw_payload),
            created_at=event.created_at,
        )
