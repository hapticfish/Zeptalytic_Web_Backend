from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.models import import_models
from app.db.models.email_delivery_events import EmailDeliveryEvent
from app.db.session import SessionLocal, engine

import_models()


def _unique_dedupe_key() -> str:
    return f"brevo:{uuid4()}"


def _cleanup_event(dedupe_key: str) -> None:
    with SessionLocal() as session:
        event = session.scalar(
            select(EmailDeliveryEvent).where(EmailDeliveryEvent.dedupe_key == dedupe_key)
        )
        if event is not None:
            session.delete(event)
            session.commit()


def test_parent_email_delivery_event_round_trip() -> None:
    dedupe_key = _unique_dedupe_key()
    event_timestamp = datetime.now(timezone.utc).replace(microsecond=0)

    try:
        with SessionLocal() as session:
            delivery_event = EmailDeliveryEvent(
                event_type="delivered",
                provider_message_id="brevo-message-rt-002",
                provider_event_id="brevo-event-rt-002",
                email="delivery_roundtrip@example.com",
                template_id=9,
                subject="Verify your email",
                event_timestamp=event_timestamp,
                dedupe_key=dedupe_key,
                raw_payload={"event": "delivered", "messageId": "brevo-message-rt-002"},
            )
            session.add(delivery_event)
            session.commit()

        with SessionLocal() as session:
            persisted_event = session.scalar(
                select(EmailDeliveryEvent).where(EmailDeliveryEvent.dedupe_key == dedupe_key)
            )

            assert persisted_event is not None
            assert persisted_event.provider == "brevo"
            assert persisted_event.event_type == "delivered"
            assert persisted_event.provider_message_id == "brevo-message-rt-002"
            assert persisted_event.provider_event_id == "brevo-event-rt-002"
            assert persisted_event.email == "delivery_roundtrip@example.com"
            assert persisted_event.template_id == 9
            assert persisted_event.subject == "Verify your email"
            assert persisted_event.event_timestamp == event_timestamp
            assert persisted_event.raw_payload == {
                "event": "delivered",
                "messageId": "brevo-message-rt-002",
            }
    finally:
        _cleanup_event(dedupe_key)


def test_parent_db_email_delivery_event_constraints_and_indexes_match_expected_contract() -> None:
    dedupe_key = _unique_dedupe_key()

    try:
        with SessionLocal() as session:
            session.add(
                EmailDeliveryEvent(
                    event_type="unknown",
                    dedupe_key=dedupe_key,
                    raw_payload={"event": "unknown"},
                )
            )
            session.commit()

            session.add(
                EmailDeliveryEvent(
                    event_type="unknown",
                    dedupe_key=dedupe_key,
                    raw_payload={"event": "unknown-duplicate"},
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

        inspector = inspect(engine)
        index_names = {index["name"] for index in inspector.get_indexes("email_delivery_events")}

        assert "ix_email_delivery_events_provider_message_id" in index_names
        assert "ix_email_delivery_events_event_type" in index_names
        assert "ix_email_delivery_events_created_at" in index_names
        assert "ux_email_delivery_events_dedupe_key" in index_names
    finally:
        _cleanup_event(dedupe_key)
