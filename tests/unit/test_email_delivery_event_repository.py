from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.email_delivery_events import EmailDeliveryEvent
from app.db.repositories.email_delivery_event_repository import EmailDeliveryEventRepository


def _create_in_memory_schema() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata = MetaData()
    EmailDeliveryEvent.__table__.to_metadata(metadata)
    metadata.create_all(engine)
    return Session(engine)


def test_email_delivery_event_model_has_expected_indexes_and_defaults() -> None:
    event_table = EmailDeliveryEvent.__table__
    index_names = {index.name for index in event_table.indexes}

    assert event_table.c.provider.server_default is not None
    assert event_table.c.raw_payload.server_default is not None
    assert "ix_email_delivery_events_provider_message_id" in index_names
    assert "ix_email_delivery_events_event_type" in index_names
    assert "ix_email_delivery_events_created_at" in index_names
    assert "ux_email_delivery_events_dedupe_key" in index_names


def test_email_delivery_event_repository_creates_and_deduplicates_events() -> None:
    session = _create_in_memory_schema()
    repository = EmailDeliveryEventRepository(session)
    event_timestamp = datetime(2026, 5, 24, 23, 15, tzinfo=UTC)

    created = repository.create_event_if_new(
        event_type="delivered",
        dedupe_key="brevo:message-1:delivered:2026-05-24T23:15:00Z",
        provider_message_id="message-1",
        provider_event_id="event-1",
        email="recipient@example.com",
        template_id=9,
        subject="Verify your email",
        event_timestamp=event_timestamp,
        raw_payload={"event": "delivered", "messageId": "message-1"},
    )

    assert created.created is True
    assert created.record.provider == "brevo"
    assert created.record.event_type == "delivered"
    assert created.record.provider_message_id == "message-1"
    assert created.record.provider_event_id == "event-1"
    assert created.record.email == "recipient@example.com"
    assert created.record.template_id == 9
    assert created.record.subject == "Verify your email"
    assert created.record.event_timestamp == event_timestamp
    assert created.record.raw_payload == {"event": "delivered", "messageId": "message-1"}

    duplicate = repository.create_event_if_new(
        event_type="delivered",
        dedupe_key="brevo:message-1:delivered:2026-05-24T23:15:00Z",
        provider_message_id="message-1",
        raw_payload={"event": "delivered", "messageId": "message-1"},
    )

    assert duplicate.created is False
    assert duplicate.record.event_id == created.record.event_id

    listed = repository.list_for_provider_message_id("message-1")
    assert len(listed) == 1
    assert listed[0].event_id == created.record.event_id


def test_email_delivery_event_repository_returns_existing_row_for_duplicate_dedupe_key() -> None:
    session = _create_in_memory_schema()
    repository = EmailDeliveryEventRepository(session)

    first = repository.create_event_if_new(
        event_type="opened",
        dedupe_key="brevo:event:event-duplicate-1",
        provider_event_id="event-duplicate-1",
        raw_payload={"event": "opened", "eventId": "event-duplicate-1"},
    )
    second = repository.create_event_if_new(
        event_type="opened",
        dedupe_key="brevo:event:event-duplicate-1",
        provider_event_id="event-duplicate-1",
        raw_payload={"event": "opened", "eventId": "event-duplicate-1"},
    )

    assert first.created is True
    assert second.created is False
    assert second.record.event_id == first.record.event_id


def test_email_delivery_events_require_event_type_and_dedupe_key() -> None:
    session = _create_in_memory_schema()

    session.add(
        EmailDeliveryEvent(
            event_type=None,  # type: ignore[arg-type]
            dedupe_key=f"brevo:{uuid4()}",
            raw_payload={"event": "delivered"},
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    session.add(
        EmailDeliveryEvent(
            event_type="unknown",
            dedupe_key=None,  # type: ignore[arg-type]
            raw_payload={"event": "unknown"},
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    session.add(
        EmailDeliveryEvent(
            event_type="unknown",
            dedupe_key=f"brevo:{uuid4()}",
            raw_payload=None,  # type: ignore[arg-type]
        )
    )
    session.commit()

    persisted_event = session.scalar(select(EmailDeliveryEvent).order_by(EmailDeliveryEvent.created_at.desc()))
    assert persisted_event is not None
    assert persisted_event.raw_payload is None
