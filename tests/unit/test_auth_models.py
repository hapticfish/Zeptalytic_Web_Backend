from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.auth import (
    Account,
    AccountSecuritySettings,
    AuthEvent,
    AuthSession,
    EmailVerificationToken,
    MfaRecoveryCode,
    PasswordResetToken,
)


def _create_in_memory_schema() -> tuple[Session, MetaData]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    metadata = MetaData()

    for table in (
        Account.__table__,
        AuthSession.__table__,
        EmailVerificationToken.__table__,
        PasswordResetToken.__table__,
        AccountSecuritySettings.__table__,
        MfaRecoveryCode.__table__,
        AuthEvent.__table__,
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
        "account_security_settings",
        "mfa_recovery_codes",
        "auth_events",
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


def test_security_tables_have_expected_defaults_and_indexes() -> None:
    security_table = AccountSecuritySettings.__table__
    recovery_code_indexes = {index.name for index in MfaRecoveryCode.__table__.indexes}
    auth_event_indexes = {index.name for index in AuthEvent.__table__.indexes}

    assert security_table.c.two_factor_enabled.server_default is not None
    assert security_table.c.recovery_methods_available_count.server_default is not None
    assert "ix_mfa_recovery_codes_account_id" in recovery_code_indexes
    assert "ix_auth_events_account_id" in auth_event_indexes
    assert "ix_auth_events_event_type" in auth_event_indexes


def test_auth_and_security_persistence_round_trip() -> None:
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
    security_settings = AccountSecuritySettings(account_id=account.id)
    recovery_code = MfaRecoveryCode(
        account_id=account.id,
        code_hash="recovery-code-hash",
    )
    auth_event = AuthEvent(
        account_id=account.id,
        event_type="login_success",
        ip_address="203.0.113.25",
        user_agent="pytest-agent",
        event_metadata={"source": "unit-test"},
    )

    session.add_all([auth_session, email_token, reset_token, security_settings, recovery_code, auth_event])
    session.commit()

    persisted_session = session.scalar(select(AuthSession).where(AuthSession.account_id == account.id))
    persisted_verify = session.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == account.id)
    )
    persisted_reset = session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.account_id == account.id)
    )
    persisted_security_settings = session.scalar(
        select(AccountSecuritySettings).where(AccountSecuritySettings.account_id == account.id)
    )
    persisted_recovery_code = session.scalar(
        select(MfaRecoveryCode).where(MfaRecoveryCode.account_id == account.id)
    )
    persisted_auth_event = session.scalar(select(AuthEvent).where(AuthEvent.account_id == account.id))

    assert persisted_session is not None
    assert persisted_session.session_token_hash == "session-token-hash"
    assert persisted_verify is not None
    assert persisted_verify.token_hash == "verify-token-hash"
    assert persisted_reset is not None
    assert persisted_reset.token_hash == "reset-token-hash"
    assert persisted_security_settings is not None
    assert persisted_security_settings.two_factor_enabled is False
    assert persisted_security_settings.recovery_methods_available_count == 0
    assert persisted_recovery_code is not None
    assert persisted_recovery_code.code_hash == "recovery-code-hash"
    assert persisted_auth_event is not None
    assert persisted_auth_event.event_type == "login_success"
    assert persisted_auth_event.event_metadata == {"source": "unit-test"}


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


def test_account_security_settings_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(AccountSecuritySettings(account_id=uuid4()))

    with pytest.raises(IntegrityError):
        session.commit()


def test_auth_events_require_event_type() -> None:
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
        AuthEvent(
            account_id=account.id,
            event_type=None,  # type: ignore[arg-type]
            event_metadata={},
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
