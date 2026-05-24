from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.models import import_models
from app.db.models.accounts import Account
from app.db.models.email_send_attempts import EmailSendAttempt
from app.db.session import SessionLocal, engine

import_models()


def _unique_suffix() -> str:
    return uuid4().hex[:12]


def _cleanup_account(account_id: UUID) -> None:
    with SessionLocal() as session:
        account = session.get(Account, account_id)
        if account is not None:
            session.delete(account)
            session.commit()


def test_parent_email_send_attempt_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None
    sent_at = datetime.now(timezone.utc).replace(microsecond=0)

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"email_attempt_{suffix}",
                email=f"email_attempt_{suffix}@example.com",
                password_hash="hashed-password",
                status="pending_verification",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            send_attempt = EmailSendAttempt(
                account_id=account.id,
                to_email=account.email,
                from_email="support@zeptalytic.com",
                from_name="Zeptalytic Support",
                reply_to_email="support@zeptalytic.com",
                template_key="email_verification",
                provider_template_id=9,
                provider_message_id="brevo-message-rt-001",
                status="sent",
                attempt_metadata={"flow": "signup", "token_type": "email_verification"},
                sent_at=sent_at,
            )
            session.add(send_attempt)
            session.commit()

        with SessionLocal() as session:
            persisted_attempt = session.scalar(
                select(EmailSendAttempt).where(EmailSendAttempt.account_id == account_id)
            )

            assert persisted_attempt is not None
            assert persisted_attempt.to_email == f"email_attempt_{suffix}@example.com"
            assert persisted_attempt.template_key == "email_verification"
            assert persisted_attempt.provider == "brevo"
            assert persisted_attempt.provider_template_id == 9
            assert persisted_attempt.provider_message_id == "brevo-message-rt-001"
            assert persisted_attempt.status == "sent"
            assert persisted_attempt.attempt_metadata == {
                "flow": "signup",
                "token_type": "email_verification",
            }
            assert persisted_attempt.sent_at == sent_at
            assert persisted_attempt.failed_at is None
    finally:
        if account_id is not None:
            _cleanup_account(account_id)


def test_parent_db_email_send_attempt_constraints_and_indexes_match_expected_contract() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"email_constraint_{suffix}",
                email=f"email_constraint_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            session.add(
                EmailSendAttempt(
                    account_id=account.id,
                    to_email=account.email,
                    from_email="support@zeptalytic.com",
                    template_key="email_verification",
                    status="pending",
                    attempt_metadata={"flow": "signup"},
                )
            )
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

        inspector = inspect(engine)
        index_names = {index["name"] for index in inspector.get_indexes("email_send_attempts")}

        assert "ix_email_send_attempts_account_id" in index_names
        assert "ix_email_send_attempts_status" in index_names
        assert "ix_email_send_attempts_provider_message_id" in index_names
        assert "ix_email_send_attempts_created_at" in index_names
    finally:
        if account_id is not None:
            _cleanup_account(account_id)
