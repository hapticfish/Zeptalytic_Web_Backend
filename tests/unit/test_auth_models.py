from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.auth import Account, AuthSession, EmailVerificationToken, PasswordResetToken


def _create_in_memory_schema() -> tuple[Session, MetaData]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata = MetaData()

    for table in (
        Account.__table__,
        AuthSession.__table__,
        EmailVerificationToken.__table__,
        PasswordResetToken.__table__,
    ):
        table.to_metadata(metadata)

    metadata.create_all(engine)
    return Session(engine), metadata


def test_auth_tables_are_registered_in_metadata() -> None:
    table_names = set(Account.metadata.tables)

    assert {
        "accounts",
        "auth_sessions",
        "email_verification_tokens",
        "password_reset_tokens",
    }.issubset(table_names)


def test_accounts_table_has_expected_constraints_and_indexes() -> None:
    accounts_table = Account.__table__
    constraint_columns = {
        tuple(sorted(column.name for column in constraint.columns))
        for constraint in accounts_table.constraints
        if getattr(constraint, "columns", None)
    }
    index_names = {index.name for index in accounts_table.indexes}

    assert ("email",) in constraint_columns
    assert ("username",) in constraint_columns
    assert "ix_accounts_status" in index_names


def test_auth_session_persistence_round_trip() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        username="tester",
        email="tester@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.flush()

    auth_session = AuthSession(
        account_id=account.id,
        session_token_hash="session-token-hash",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        ip_address="203.0.113.25",
        user_agent="pytest-agent",
    )
    email_token = EmailVerificationToken(
        account_id=account.id,
        token_hash="verify-token-hash",
        expires_at=datetime.now(UTC) + timedelta(hours=12),
    )
    reset_token = PasswordResetToken(
        account_id=account.id,
        token_hash="reset-token-hash",
        expires_at=datetime.now(UTC) + timedelta(hours=2),
    )

    session.add_all([auth_session, email_token, reset_token])
    session.commit()

    persisted_session = session.scalar(select(AuthSession).where(AuthSession.account_id == account.id))
    persisted_verify = session.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == account.id)
    )
    persisted_reset = session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.account_id == account.id)
    )

    assert persisted_session is not None
    assert persisted_session.session_token_hash == "session-token-hash"
    assert persisted_verify is not None
    assert persisted_verify.token_hash == "verify-token-hash"
    assert persisted_reset is not None
    assert persisted_reset.token_hash == "reset-token-hash"


def test_accounts_reject_duplicate_email() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        Account(
            username="tester-1",
            email="duplicate@example.com",
            password_hash="hash-1",
            status="active",
            role="member",
        )
    )
    session.commit()

    session.add(
        Account(
            username="tester-2",
            email="duplicate@example.com",
            password_hash="hash-2",
            status="active",
            role="member",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_auth_sessions_require_token_hash() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        AuthSession(
            account_id=account.id,
            session_token_hash=None,  # type: ignore[arg-type]
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
