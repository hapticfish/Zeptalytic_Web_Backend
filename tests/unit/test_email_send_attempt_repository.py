from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.email_send_attempts import EmailSendAttempt
from app.db.repositories.email_send_attempt_repository import (
    EmailSendAttemptRepository,
    sanitize_email_send_attempt_metadata,
)


def _create_in_memory_schema() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    metadata = MetaData()
    for table in (Account.__table__, EmailSendAttempt.__table__):
        table.to_metadata(metadata)

    metadata.create_all(engine)
    return Session(engine)


def test_email_send_attempt_model_has_expected_defaults_and_indexes() -> None:
    attempt_table = EmailSendAttempt.__table__
    index_names = {index.name for index in attempt_table.indexes}

    assert attempt_table.c.provider.server_default is not None
    assert attempt_table.c.metadata.server_default is not None
    assert "ix_email_send_attempts_account_id" in index_names
    assert "ix_email_send_attempts_status" in index_names
    assert "ix_email_send_attempts_provider_message_id" in index_names
    assert "ix_email_send_attempts_created_at" in index_names


def test_email_send_attempt_repository_creates_and_updates_attempt_statuses() -> None:
    session = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="email-attempt-owner",
        email="email-attempt-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    repository = EmailSendAttemptRepository(session)
    created = repository.create_send_attempt(
        account_id=account.id,
        to_email="recipient@example.com",
        from_email="support@zeptalytic.com",
        from_name="Zeptalytic Support",
        reply_to_email="support@zeptalytic.com",
        template_key="email_verification",
        provider_template_id=9,
        status="pending",
        metadata={
            "flow": "signup",
            "token_type": "email_verification",
            "verification_url": "https://example.com/verify-email?token=secret-token",
        },
    )

    assert created.account_id == account.id
    assert created.status == "pending"
    assert created.provider == "brevo"
    assert created.provider_template_id == 9
    assert created.metadata == {"flow": "signup", "token_type": "email_verification"}

    sent = repository.mark_sent(
        created.attempt_id,
        provider_message_id="brevo-message-123",
        sent_at=datetime(2026, 5, 24, 22, 0, tzinfo=UTC),
    )

    assert sent is not None
    assert sent.status == "sent"
    assert sent.provider_message_id == "brevo-message-123"
    assert sent.sent_at == datetime(2026, 5, 24, 22, 0, tzinfo=UTC)
    assert sent.failed_at is None

    failed = repository.mark_failed(
        created.attempt_id,
        failure_code="provider_http_error",
        failure_message="Brevo request failed.",
        failed_at=datetime(2026, 5, 24, 22, 5, tzinfo=UTC),
    )

    assert failed is not None
    assert failed.status == "failed"
    assert failed.failure_code == "provider_http_error"
    assert failed.failure_message == "Brevo request failed."
    assert failed.failed_at == datetime(2026, 5, 24, 22, 5, tzinfo=UTC)

    skipped = repository.mark_skipped(
        created.attempt_id,
        failure_code="provider_disabled",
        failure_message="Email sending disabled in this environment.",
    )

    assert skipped is not None
    assert skipped.status == "skipped"
    assert skipped.failure_code == "provider_disabled"
    assert skipped.failure_message == "Email sending disabled in this environment."


def test_email_send_attempt_metadata_sanitizer_drops_forbidden_token_and_secret_fields() -> None:
    sanitized = sanitize_email_send_attempt_metadata(
        {
            "flow": "forgot_password",
            "verification_token": "raw-token",
            "reset_url": "https://example.com/reset-password?token=raw-token",
            "nested": {
                "webhook_secret": "top-secret",
                "allowed": "value",
            },
            "events": [
                {"kind": "queued", "api_key": "xkeysib-secret"},
                "https://example.com/verify-email?token=raw-token",
                "safe-value",
            ],
        }
    )

    assert sanitized == {
        "flow": "forgot_password",
        "nested": {"allowed": "value"},
        "events": [{"kind": "queued"}, "safe-value"],
    }


def test_email_send_attempts_require_recipient_and_status() -> None:
    session = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="email-send-attempt-owner",
        email="email-send-attempt-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        EmailSendAttempt(
            account_id=account.id,
            to_email=None,  # type: ignore[arg-type]
            from_email="support@zeptalytic.com",
            template_key="email_verification",
            status="pending",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    session.add(
        EmailSendAttempt(
            account_id=account.id,
            to_email="recipient@example.com",
            from_email="support@zeptalytic.com",
            template_key="email_verification",
            status=None,  # type: ignore[arg-type]
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
