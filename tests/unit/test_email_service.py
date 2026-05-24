from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import import_models
from app.db.models.accounts import Account
from app.db.models.email_send_attempts import EmailSendAttempt
from app.db.repositories.email_send_attempt_repository import EmailSendAttemptRepository
from app.integrations import BrevoSendEmailResult
from app.services.email_service import EmailService, build_email_service


@dataclass
class StubBrevoClient:
    result: BrevoSendEmailResult
    captured_requests: list[object]

    def send_template_email(self, request):  # noqa: ANN001
        self.captured_requests.append(request)
        return self.result


def _build_session() -> Session:
    import_models()

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


def _create_account(session: Session, *, suffix: str = "email-service") -> Account:
    account = Account(
        id=uuid4(),
        username=f"{suffix}-user",
        email=f"{suffix}@example.com",
        password_hash="hashed-password",
        status="active",
        role="user",
    )
    session.add(account)
    session.commit()
    return account


def _build_settings(**overrides: object) -> Settings:
    values = {
        "email_provider": "brevo",
        "frontend_base_url": "https://frontend.example.com",
        "email_from_address": "hello@example.com",
        "email_from_name": "Zeptalytic",
        "email_reply_to_address": "support@example.com",
        "email_support_from_address": "support@example.com",
        "email_billing_from_address": "billing@example.com",
        "email_alerts_from_address": "alerts@example.com",
        "email_updates_from_address": "updates@example.com",
        "brevo_template_welcome_id": 101,
        "brevo_template_support_response_id": 102,
        "brevo_template_order_confirmation_id": 103,
        "brevo_template_news_updates_id": 104,
        "brevo_template_failed_signup_id": 105,
        "brevo_template_email_changed_id": 106,
        "brevo_template_password_reset_id": 107,
        "brevo_template_account_details_changed_id": 108,
        "brevo_template_email_verification_id": 109,
        "brevo_template_payment_failed_id": 110,
        "brevo_template_subscription_expiring_id": 111,
    }
    values.update(overrides)
    return Settings(**values)


def _persisted_attempt(session: Session, attempt_id: UUID) -> EmailSendAttempt:
    attempt = session.get(EmailSendAttempt, attempt_id)
    assert attempt is not None
    return attempt


def test_email_service_records_successful_signup_verification_send_without_persisting_token_url() -> None:
    session = _build_session()
    account = _create_account(session)
    brevo_client = StubBrevoClient(
        result=BrevoSendEmailResult(provider_message_id="<message-id@example.test>", status_code=201),
        captured_requests=[],
    )

    service = build_email_service(
        session,
        brevo_client,
        app_settings=_build_settings(),
    )

    result = service.send_signup_verification(
        account_id=account.id,
        to_email=account.email,
        verification_url="https://frontend.example.com/verify-email?token=raw-token",
        display_name="Example User",
    )

    assert result.success is True
    assert result.template_key.value == "email_verification"
    assert result.provider_template_id == 109
    assert result.provider_message_id == "<message-id@example.test>"

    captured_request = brevo_client.captured_requests[0]
    assert captured_request.template_id == 109
    assert captured_request.sender_email == "support@example.com"
    assert captured_request.reply_to_email == "support@example.com"
    assert captured_request.to_email == account.email
    assert captured_request.params["verificationUrl"] == "https://frontend.example.com/verify-email?token=raw-token"

    persisted_attempt = _persisted_attempt(session, result.attempt_id)
    assert persisted_attempt.status == "sent"
    assert persisted_attempt.provider_message_id == "<message-id@example.test>"
    assert persisted_attempt.from_email == "support@example.com"
    assert persisted_attempt.reply_to_email == "support@example.com"
    assert persisted_attempt.provider_template_id == 109
    assert persisted_attempt.attempt_metadata == {
        "flow": "signup",
        "token_type": "email_verification",
        "has_verification_url": True,
    }


def test_email_service_records_failed_password_reset_send() -> None:
    session = _build_session()
    account = _create_account(session, suffix="password-reset")
    brevo_client = StubBrevoClient(
        result=BrevoSendEmailResult(
            provider_message_id=None,
            failure_code="provider_http_error",
            failure_message="Brevo request failed.",
            status_code=500,
        ),
        captured_requests=[],
    )
    service = build_email_service(
        session,
        brevo_client,
        app_settings=_build_settings(),
    )

    result = service.send_password_reset(
        account_id=account.id,
        to_email=account.email,
        reset_url="https://frontend.example.com/reset-password?token=raw-token",
        display_name=None,
    )

    assert result.success is False
    assert result.status == "failed"
    assert result.failure_code == "provider_http_error"
    assert result.failure_message == "Brevo request failed."
    assert result.provider_template_id == 107

    persisted_attempt = _persisted_attempt(session, result.attempt_id)
    assert persisted_attempt.status == "failed"
    assert persisted_attempt.failure_code == "provider_http_error"
    assert persisted_attempt.failure_message == "Brevo request failed."
    assert persisted_attempt.attempt_metadata == {
        "flow": "forgot_password",
        "token_type": "password_reset",
        "has_reset_url": True,
    }


def test_email_service_marks_attempt_failed_when_brevo_client_is_missing() -> None:
    session = _build_session()
    account = _create_account(session, suffix="missing-client")
    service = EmailService(
        repository=EmailSendAttemptRepository(session),
        brevo_client=None,
        app_settings=_build_settings(),
    )

    result = service.send_welcome(
        account_id=account.id,
        to_email=account.email,
        display_name="Welcome User",
    )

    assert result.success is False
    assert result.status == "failed"
    assert result.failure_code == "provider_invalid_config"

    persisted_attempt = _persisted_attempt(session, result.attempt_id)
    assert persisted_attempt.status == "failed"
    assert persisted_attempt.failure_code == "provider_invalid_config"
    assert persisted_attempt.from_email == "hello@example.com"
    assert persisted_attempt.reply_to_email == "support@example.com"
    assert persisted_attempt.provider_template_id == 101


def test_email_service_uses_support_sender_for_account_details_changed_notifications() -> None:
    session = _build_session()
    account = _create_account(session, suffix="account-details")
    brevo_client = StubBrevoClient(
        result=BrevoSendEmailResult(provider_message_id="account-details-1", status_code=201),
        captured_requests=[],
    )
    service = build_email_service(
        session,
        brevo_client,
        app_settings=_build_settings(),
    )

    result = service.send_account_details_changed(
        account_id=account.id,
        to_email=account.email,
        display_name="Account User",
        change_summary="Password updated",
        changed_at=datetime(2026, 5, 24, 22, 30, tzinfo=timezone.utc),
    )

    assert result.success is True
    assert result.provider_template_id == 108

    captured_request = brevo_client.captured_requests[0]
    assert captured_request.sender_email == "support@example.com"
    assert captured_request.reply_to_email == "support@example.com"
    assert captured_request.params["changeSummary"] == "Password updated"
    assert captured_request.params["changedAt"] == "2026-05-24T22:30:00+00:00"
