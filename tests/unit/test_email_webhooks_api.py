from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.api.routers.v1.email_webhooks import _build_dedupe_key, _normalize_event_type
from app.db.models.email_delivery_events import EmailDeliveryEvent
from app.main import app
from tests.unit.assertions import assert_standard_error_response


def _create_in_memory_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata = MetaData()
    EmailDeliveryEvent.__table__.to_metadata(metadata)
    metadata.create_all(engine)
    return Session(engine)


@contextmanager
def _webhook_client(*, webhook_secret: str = "test-webhook-secret") -> Iterator[tuple[TestClient, Session]]:
    from app.core.config import settings

    session = _create_in_memory_session()
    previous_secret = settings.brevo_webhook_secret
    settings.brevo_webhook_secret = webhook_secret

    def override_get_db() -> Iterator[Session]:
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_db, None)
        settings.brevo_webhook_secret = previous_secret
        session.close()


def test_brevo_webhook_rejects_missing_secret() -> None:
    with _webhook_client() as (client, session):
        response = client.post("/api/v1/email/webhooks/brevo", json={"event": "delivered"})
        stored_events = session.scalars(select(EmailDeliveryEvent)).all()

    assert_standard_error_response(
        response,
        status_code=401,
        code="invalid_webhook_secret",
        message="Webhook authentication failed.",
        details={},
    )
    assert stored_events == []


def test_brevo_webhook_rejects_invalid_secret() -> None:
    with _webhook_client() as (client, session):
        response = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "wrong-secret"},
            json={"event": "delivered"},
        )
        stored_events = session.scalars(select(EmailDeliveryEvent)).all()

    assert_standard_error_response(
        response,
        status_code=401,
        code="invalid_webhook_secret",
        message="Webhook authentication failed.",
        details={},
    )
    assert stored_events == []


def test_brevo_webhook_accepts_valid_secret_and_stores_event() -> None:
    with _webhook_client() as (client, session):
        response = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            json={
                "event": "delivered",
                "messageId": "brevo-message-1",
                "eventId": "brevo-event-1",
                "email": "recipient@example.com",
                "templateId": 9,
                "subject": "Verify your email",
                "date": "2026-05-24T23:15:00Z",
            },
        )

        stored_events = session.scalars(select(EmailDeliveryEvent)).all()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert len(stored_events) == 1
    assert stored_events[0].provider == "brevo"
    assert stored_events[0].event_type == "delivered"
    assert stored_events[0].provider_message_id == "brevo-message-1"
    assert stored_events[0].provider_event_id == "brevo-event-1"
    assert stored_events[0].email == "recipient@example.com"
    assert stored_events[0].template_id == 9


def test_brevo_webhook_returns_success_for_duplicate_payload() -> None:
    payload = {
        "event": "delivered",
        "messageId": "brevo-message-2",
        "email": "duplicate@example.com",
    }

    with _webhook_client() as (client, session):
        first = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            json=payload,
        )
        second = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            json=payload,
        )
        stored_events = session.scalars(select(EmailDeliveryEvent)).all()

    assert first.status_code == 200
    assert first.json() == {"status": "ok"}
    assert second.status_code == 200
    assert second.json() == {"status": "duplicate"}
    assert len(stored_events) == 1


def test_brevo_webhook_normalizes_supported_event_names() -> None:
    assert _normalize_event_type({"event": "sent"}) == "sent"
    assert _normalize_event_type({"event": "delivered"}) == "delivered"
    assert _normalize_event_type({"event": "open"}) == "opened"
    assert _normalize_event_type({"event": "clicked"}) == "clicked"
    assert _normalize_event_type({"event": "softBounce"}) == "soft_bounce"
    assert _normalize_event_type({"event": "hard-bounce"}) == "hard_bounce"
    assert _normalize_event_type({"event": "invalid"}) == "invalid_email"
    assert _normalize_event_type({"event": "deferred"}) == "deferred"
    assert _normalize_event_type({"event": "spam"}) == "complaint"
    assert _normalize_event_type({"event": "unsubscribed"}) == "unsubscribed"
    assert _normalize_event_type({"event": "blocked"}) == "blocked"
    assert _normalize_event_type({"event": "error"}) == "error"
    assert _normalize_event_type({"event": "mystery_signal"}) == "unknown"


def test_brevo_webhook_builds_provider_event_id_dedupe_key() -> None:
    dedupe_key = _build_dedupe_key(
        {
            "event": "delivered",
            "eventId": "brevo-event-strong-key",
            "messageId": "brevo-message-3",
            "email": "recipient@example.com",
        }
    )

    assert dedupe_key == "brevo:event:brevo-event-strong-key"


def test_brevo_webhook_builds_message_scoped_dedupe_key_without_provider_event_id() -> None:
    dedupe_key = _build_dedupe_key(
        {
            "event": "click",
            "messageId": "brevo-message-4",
            "email": "recipient@example.com",
            "templateId": "9",
            "date": "2026-05-24T23:15:00Z",
        }
    )

    assert (
        dedupe_key
        == "brevo:message:brevo-message-4:clicked:recipient@example.com:9:2026-05-24T23:15:00Z"
    )


def test_brevo_webhook_stores_unknown_event_type_without_requiring_session() -> None:
    with _webhook_client() as (client, session):
        response = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            json={"event": "mystery_signal", "email": "unknown@example.com"},
        )
        stored_event = session.scalar(select(EmailDeliveryEvent))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert stored_event is not None
    assert stored_event.event_type == "unknown"
    assert stored_event.email == "unknown@example.com"


def test_brevo_webhook_rejects_malformed_json_payload() -> None:
    with _webhook_client() as (client, _session):
        response = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            content="{",
            headers={"content-type": "application/json"},
        )

    assert_standard_error_response(
        response,
        status_code=400,
        code="invalid_webhook_payload",
        message="Webhook payload must be valid JSON.",
        details={},
    )


def test_brevo_webhook_rejects_non_object_payload() -> None:
    with _webhook_client() as (client, _session):
        response = client.post(
            "/api/v1/email/webhooks/brevo",
            params={"secret": "test-webhook-secret"},
            json=["not", "an", "object"],
        )

    assert_standard_error_response(
        response,
        status_code=400,
        code="invalid_webhook_payload",
        message="Webhook payload must be a JSON object.",
        details={},
    )
