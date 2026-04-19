from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.orm import Session

from app.db.models.account_security_settings import AccountSecuritySettings
from app.db.models.accounts import Account
from app.db.models.auth_events import AuthEvent
from app.db.models.auth_sessions import AuthSession
from app.db.models.communication_preferences import CommunicationPreference
from app.db.models.email_verification_tokens import EmailVerificationToken
from app.db.models.mfa_recovery_codes import MfaRecoveryCode
from app.db.models.password_reset_tokens import PasswordResetToken
from app.db.models.profile_preferences import ProfilePreference
from app.db.models.profiles import Profile
from app.db.repositories.auth_repository import AuthRepository
from app.services.auth_service import (
    AccountAccessRestrictedError,
    AuthClientInfo,
    CurrentPasswordInvalidError,
    AuthService,
    DuplicateAccountError,
    EmailVerificationRequiredError,
    EmailVerificationTokenInvalidError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
    SessionNotFoundError,
    TwoFactorAlreadyEnabledError,
    TwoFactorCodeInvalidError,
    TwoFactorNotEnabledError,
)


class StubParentAccountLinker:
    def __init__(self) -> None:
        self.account_ids: list = []

    def ensure_account_link(self, account_id) -> None:  # noqa: ANN001
        self.account_ids.append(account_id)


def _create_in_memory_session() -> Session:
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
        Profile.__table__,
        ProfilePreference.__table__,
        CommunicationPreference.__table__,
    ):
        table.to_metadata(metadata)

    metadata.create_all(engine)
    return Session(engine)


def _build_service(
    session: Session,
    *,
    parent_account_linker: StubParentAccountLinker | None = None,
) -> AuthService:
    return AuthService(
        AuthRepository(session),
        session,
        session_ttl_hours=12,
        parent_account_linker=parent_account_linker,
    )


def _client_info() -> AuthClientInfo:
    return AuthClientInfo(ip_address="127.0.0.1", user_agent="pytest")


def _totp_code(service: AuthService, account_id) -> str:  # noqa: ANN001
    secret = service._derive_totp_secret(account_id)  # type: ignore[attr-defined]
    counter = int(datetime.now(timezone.utc).timestamp() // 30)
    return service._generate_totp_code(secret=secret, counter=counter)  # type: ignore[attr-defined]


def _persist_account(
    session: Session,
    *,
    email: str = "existing@example.com",
    username: str = "existing-user",
    status: str = "active",
) -> Account:
    account = Account(
        id=uuid4(),
        username=username,
        email=email,
        password_hash=AuthService._hash_password("Password123"),  # type: ignore[attr-defined]
        status=status,
        role="user",
        email_verified_at=datetime.now(timezone.utc) if status == "active" else None,
    )
    session.add(account)
    session.commit()
    return account


def test_auth_service_returns_context_for_active_unrevoked_session() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="session-owner",
        email="owner@example.com",
        password="Password123",
        client_info=_client_info(),
    )

    context = service.get_authenticated_session_context(signup_result.session_token)

    assert context is not None
    assert context.username == "session-owner"
    assert context.email == "owner@example.com"


def test_auth_service_rejects_expired_or_revoked_session_records() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="expiring-user",
        email="expiring@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    persisted_session = session.scalar(select(AuthSession))
    assert persisted_session is not None
    persisted_session.expires_at = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
    session.commit()

    assert service.get_authenticated_session_context(signup_result.session_token) is None

    persisted_session.expires_at = datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc)
    persisted_session.revoked_at = datetime.now(timezone.utc)
    session.commit()

    assert service.get_authenticated_session_context(signup_result.session_token) is None


def test_auth_service_requires_verified_email_for_normal_actions() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    result = service.signup(
        username="pending-user",
        email="pending@example.com",
        password="Password123",
        client_info=_client_info(),
    )

    pending_context = AuthService.ensure_account_status_allows_authenticated_access(result.context)

    with pytest.raises(EmailVerificationRequiredError):
        service.ensure_email_verified(pending_context)


def test_auth_service_blocks_suspended_and_closed_accounts_from_normal_actions() -> None:
    suspended_context = AuthService._build_context(  # type: ignore[attr-defined]
        AuthRepository.build_session_account_record(
            account=Account(
                id=uuid4(),
                username="suspended-user",
                email="suspended@example.com",
                password_hash="hash",
                status="suspended",
                role="user",
                email_verified_at=datetime.now(timezone.utc),
            ),
            auth_session=AuthSession(
                id=uuid4(),
                account_id=uuid4(),
                session_token_hash="hash",
                expires_at=datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc),
            ),
        )
    )
    closed_context = AuthService._build_context(  # type: ignore[attr-defined]
        AuthRepository.build_session_account_record(
            account=Account(
                id=uuid4(),
                username="closed-user",
                email="closed@example.com",
                password_hash="hash",
                status="closed",
                role="user",
                email_verified_at=datetime.now(timezone.utc),
            ),
            auth_session=AuthSession(
                id=uuid4(),
                account_id=uuid4(),
                session_token_hash="hash",
                expires_at=datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc),
            ),
        )
    )

    with pytest.raises(AccountAccessRestrictedError) as suspended_error:
        AuthService.ensure_account_status_allows_normal_authenticated_actions(suspended_context)
    with pytest.raises(AccountAccessRestrictedError) as closed_error:
        AuthService.ensure_account_status_allows_authenticated_access(closed_context)

    assert suspended_error.value.status == "suspended"
    assert closed_error.value.status == "closed"


def test_signup_creates_parent_auth_state_session_and_auth_event() -> None:
    session = _create_in_memory_session()
    parent_account_linker = StubParentAccountLinker()
    service = _build_service(session, parent_account_linker=parent_account_linker)

    result = service.signup(
        username="new-user",
        email="NEW-USER@example.com",
        password="Password123",
        client_info=_client_info(),
    )

    persisted_account = session.scalar(select(Account).where(Account.email == "new-user@example.com"))
    assert persisted_account is not None
    persisted_session = session.scalar(select(AuthSession).where(AuthSession.account_id == persisted_account.id))
    persisted_event = session.scalar(select(AuthEvent).where(AuthEvent.account_id == persisted_account.id))
    persisted_security_settings = session.get(AccountSecuritySettings, persisted_account.id)
    persisted_profile = session.get(Profile, persisted_account.id)
    persisted_profile_preferences = session.get(ProfilePreference, persisted_account.id)
    persisted_communication_preferences = session.get(CommunicationPreference, persisted_account.id)
    persisted_token = session.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == persisted_account.id)
    )

    assert persisted_account.status == "pending_verification"
    assert persisted_account.role == "user"
    assert persisted_account.password_hash != "Password123"
    assert persisted_account.last_login_at is not None
    assert persisted_session is not None
    assert persisted_session.session_token_hash != result.session_token
    assert persisted_event is not None
    assert persisted_event.event_type == "signup_success"
    assert persisted_security_settings is not None
    assert persisted_profile is not None
    assert persisted_profile.display_name == "new-user"
    assert persisted_profile_preferences is not None
    assert persisted_communication_preferences is not None
    assert persisted_token is not None
    assert persisted_token.token_hash
    assert parent_account_linker.account_ids == [persisted_account.id]


def test_signup_rejects_duplicate_username_or_email() -> None:
    session = _create_in_memory_session()
    _persist_account(session)
    service = _build_service(session)

    with pytest.raises(DuplicateAccountError) as exc:
        service.signup(
            username="existing-user",
            email="existing@example.com",
            password="Password123",
            client_info=_client_info(),
        )

    assert exc.value.conflicts == ["username", "email"]


def test_login_creates_session_and_records_login_success() -> None:
    session = _create_in_memory_session()
    account = _persist_account(session, email="login@example.com", username="login-user")
    service = _build_service(session)

    result = service.login(
        email="LOGIN@example.com",
        password="Password123",
        client_info=_client_info(),
    )

    persisted_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == account.id)
    ).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == account.id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert len(persisted_sessions) == 1
    assert persisted_sessions[0].session_token_hash != result.session_token
    assert persisted_events[-1].event_type == "login_success"


def test_login_rejects_invalid_credentials_and_records_failure_for_known_account() -> None:
    session = _create_in_memory_session()
    account = _persist_account(session, email="known@example.com", username="known-user")
    service = _build_service(session)

    with pytest.raises(InvalidCredentialsError):
        service.login(
            email="known@example.com",
            password="WrongPassword123",
            client_info=_client_info(),
        )

    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == account.id)
    ).all()
    assert [event.event_type for event in persisted_events] == ["login_failed_invalid_credentials"]


def test_login_rejects_closed_account_and_records_failure() -> None:
    session = _create_in_memory_session()
    account = _persist_account(
        session,
        email="closed@example.com",
        username="closed-user",
        status="closed",
    )
    service = _build_service(session)

    with pytest.raises(AccountAccessRestrictedError) as exc:
        service.login(
            email="closed@example.com",
            password="Password123",
            client_info=_client_info(),
        )

    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == account.id)
    ).all()
    assert exc.value.status == "closed"
    assert [event.event_type for event in persisted_events] == ["login_failed_account_closed"]


def test_logout_revokes_current_session_and_records_event() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="logout-user",
        email="logout@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    current_context = service.get_authenticated_session_context(signup_result.session_token)
    assert current_context is not None

    service.login(
        email="logout@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    service.logout(
        context=current_context,
        client_info=_client_info(),
        revoke_all_sessions=True,
    )

    persisted_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == current_context.account_id)
    ).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == current_context.account_id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert all(persisted_session.revoked_at is not None for persisted_session in persisted_sessions)
    assert persisted_events[-1].event_type == "logout_success"
    assert persisted_events[-1].event_metadata == {"revoke_all_sessions": True}


def test_verify_email_marks_account_active_and_token_used() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    service.signup(
        username="verify-user",
        email="verify@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    persisted_account = session.scalar(select(Account).where(Account.email == "verify@example.com"))
    assert persisted_account is not None
    persisted_token = session.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == persisted_account.id)
    )
    assert persisted_token is not None

    verification_secret = "verify-secret"
    persisted_token.token_hash = AuthService._hash_secret(verification_secret)  # type: ignore[attr-defined]
    session.commit()

    service.verify_email(
        token=verification_secret,
        client_info=_client_info(),
    )

    session.refresh(persisted_account)
    session.refresh(persisted_token)
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == persisted_account.id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert persisted_account.status == "active"
    assert persisted_account.email_verified_at is not None
    assert persisted_token.used_at is not None
    assert persisted_events[-1].event_type == "email_verification_completed"


def test_verify_email_rejects_expired_or_used_tokens() -> None:
    session = _create_in_memory_session()
    account = _persist_account(
        session,
        email="pending-verify@example.com",
        username="pending-verify-user",
        status="pending_verification",
    )
    session.add_all(
        [
            EmailVerificationToken(
                account_id=account.id,
                token_hash=AuthService._hash_secret("expired-token"),  # type: ignore[attr-defined]
                expires_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            ),
            EmailVerificationToken(
                account_id=account.id,
                token_hash=AuthService._hash_secret("used-token"),  # type: ignore[attr-defined]
                expires_at=datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc),
                used_at=datetime.now(timezone.utc),
            ),
        ]
    )
    session.commit()
    service = _build_service(session)

    with pytest.raises(EmailVerificationTokenInvalidError) as expired_error:
        service.verify_email(token="expired-token", client_info=_client_info())
    with pytest.raises(EmailVerificationTokenInvalidError) as used_error:
        service.verify_email(token="used-token", client_info=_client_info())

    assert expired_error.value.reason == "expired"
    assert used_error.value.reason == "used"


def test_resend_email_verification_creates_new_token_for_unverified_session() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="resend-user",
        email="resend@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    initial_tokens = session.scalars(select(EmailVerificationToken)).all()
    assert context is not None

    service.resend_email_verification(
        context=context,
        client_info=_client_info(),
    )

    persisted_tokens = session.scalars(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == context.account_id)
    ).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == context.account_id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert len(initial_tokens) == 1
    assert len(persisted_tokens) == 2
    assert all(token.token_hash for token in persisted_tokens)
    assert persisted_events[-1].event_type == "email_verification_resent"


def test_forgot_password_is_enumeration_safe_for_unknown_email() -> None:
    session = _create_in_memory_session()
    known_account = _persist_account(session, email="known@example.com", username="known-user")
    service = _build_service(session)

    service.forgot_password(
        email="missing@example.com",
        client_info=_client_info(),
    )

    persisted_tokens = session.scalars(select(PasswordResetToken)).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == known_account.id)
    ).all()

    assert persisted_tokens == []
    assert persisted_events == []


def test_forgot_password_creates_reset_token_for_known_account() -> None:
    session = _create_in_memory_session()
    account = _persist_account(session, email="forgot@example.com", username="forgot-user")
    service = _build_service(session)

    service.forgot_password(
        email="FORGOT@example.com",
        client_info=_client_info(),
    )

    persisted_token = session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.account_id == account.id)
    )
    persisted_event = session.scalar(
        select(AuthEvent)
        .where(AuthEvent.account_id == account.id)
        .order_by(AuthEvent.created_at.desc())
    )

    assert persisted_token is not None
    assert persisted_token.token_hash
    assert persisted_event is not None
    assert persisted_event.event_type == "password_reset_requested"


def test_reset_password_updates_password_revokes_sessions_and_marks_token_used() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="reset-user",
        email="reset@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    account = session.scalar(select(Account).where(Account.email == "reset@example.com"))
    assert account is not None
    service.login(
        email="reset@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    reset_token = PasswordResetToken(
        account_id=account.id,
        token_hash=AuthService._hash_secret("reset-secret"),  # type: ignore[attr-defined]
        expires_at=datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc),
    )
    session.add(reset_token)
    session.commit()
    previous_password_hash = account.password_hash

    service.reset_password(
        token="reset-secret",
        new_password="NewPassword123",
        client_info=_client_info(),
    )

    session.refresh(account)
    session.refresh(reset_token)
    persisted_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == account.id)
    ).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == account.id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert account.password_hash != previous_password_hash
    assert AuthService._verify_password("NewPassword123", account.password_hash)  # type: ignore[attr-defined]
    assert reset_token.used_at is not None
    assert all(persisted_session.revoked_at is not None for persisted_session in persisted_sessions)
    assert persisted_events[-1].event_type == "password_reset_completed"
    assert service.get_authenticated_session_context(signup_result.session_token) is None


def test_reset_password_rejects_invalid_expired_or_used_tokens() -> None:
    session = _create_in_memory_session()
    account = _persist_account(session, email="reset-fail@example.com", username="reset-fail-user")
    session.add_all(
        [
            PasswordResetToken(
                account_id=account.id,
                token_hash=AuthService._hash_secret("expired-reset"),  # type: ignore[attr-defined]
                expires_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            ),
            PasswordResetToken(
                account_id=account.id,
                token_hash=AuthService._hash_secret("used-reset"),  # type: ignore[attr-defined]
                expires_at=datetime(2099, 4, 18, 12, 0, tzinfo=timezone.utc),
                used_at=datetime.now(timezone.utc),
            ),
        ]
    )
    session.commit()
    service = _build_service(session)

    with pytest.raises(PasswordResetTokenInvalidError) as invalid_error:
        service.reset_password(
            token="missing-reset",
            new_password="NewPassword123",
            client_info=_client_info(),
        )
    with pytest.raises(PasswordResetTokenInvalidError) as expired_error:
        service.reset_password(
            token="expired-reset",
            new_password="NewPassword123",
            client_info=_client_info(),
        )
    with pytest.raises(PasswordResetTokenInvalidError) as used_error:
        service.reset_password(
            token="used-reset",
            new_password="NewPassword123",
            client_info=_client_info(),
        )

    assert invalid_error.value.reason == "invalid"
    assert expired_error.value.reason == "expired"
    assert used_error.value.reason == "used"


def test_change_password_validates_current_password_and_rotates_session() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="change-user",
        email="change@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    assert context is not None
    service.login(
        email="change@example.com",
        password="Password123",
        client_info=_client_info(),
    )

    result = service.change_password(
        context=context,
        current_password="Password123",
        new_password="NewPassword123",
        client_info=_client_info(),
    )

    account = session.scalar(select(Account).where(Account.email == "change@example.com"))
    assert account is not None
    persisted_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == account.id).order_by(AuthSession.created_at.asc())
    ).all()
    persisted_events = session.scalars(
        select(AuthEvent).where(AuthEvent.account_id == account.id).order_by(AuthEvent.created_at.asc())
    ).all()

    assert AuthService._verify_password("NewPassword123", account.password_hash)  # type: ignore[attr-defined]
    assert len(persisted_sessions) == 3
    assert persisted_sessions[0].revoked_at is not None
    assert persisted_sessions[1].revoked_at is not None
    assert persisted_sessions[2].revoked_at is None
    assert persisted_sessions[2].session_token_hash != result.session_token
    assert persisted_events[-1].event_type == "password_change_completed"
    assert service.get_authenticated_session_context(signup_result.session_token) is None
    assert service.get_authenticated_session_context(result.session_token) is not None


def test_change_password_rejects_invalid_current_password() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="bad-change-user",
        email="bad-change@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    assert context is not None

    with pytest.raises(CurrentPasswordInvalidError):
        service.change_password(
            context=context,
            current_password="WrongPassword123",
            new_password="NewPassword123",
            client_info=_client_info(),
        )


def test_two_factor_enable_challenge_and_recovery_code_flow() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="mfa-user",
        email="mfa@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    assert context is not None

    enrollment = service.begin_two_factor_enrollment(context=context)
    recovery_codes = service.enable_two_factor(
        context=context,
        code=_totp_code(service, context.account_id),
        client_info=_client_info(),
    )

    refreshed_context = service.get_authenticated_session_context(signup_result.session_token)
    assert refreshed_context is not None
    assert enrollment.secret
    assert enrollment.otpauth_uri.startswith("otpauth://totp/")
    assert len(recovery_codes) == 8
    assert refreshed_context.two_factor_enabled is True
    assert refreshed_context.two_factor_method == "totp"
    assert refreshed_context.recovery_methods_available_count == 8

    service.challenge_two_factor(
        context=refreshed_context,
        code=None,
        recovery_code=recovery_codes[0],
        client_info=_client_info(),
    )
    second_context = service.get_authenticated_session_context(signup_result.session_token)
    assert second_context is not None
    assert second_context.recovery_methods_available_count == 7

    with pytest.raises(TwoFactorCodeInvalidError) as used_error:
        service.challenge_two_factor(
            context=second_context,
            code=None,
            recovery_code=recovery_codes[0],
            client_info=_client_info(),
        )

    assert used_error.value.reason == "used"


def test_two_factor_disable_requires_enabled_configuration() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="no-mfa-user",
        email="no-mfa@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    assert context is not None

    with pytest.raises(TwoFactorNotEnabledError):
        service.disable_two_factor(
            context=context,
            current_password="Password123",
            code="123456",
            recovery_code=None,
            client_info=_client_info(),
        )


def test_two_factor_cannot_be_enabled_twice() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="double-mfa-user",
        email="double-mfa@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    context = service.get_authenticated_session_context(signup_result.session_token)
    assert context is not None
    service.enable_two_factor(
        context=context,
        code=_totp_code(service, context.account_id),
        client_info=_client_info(),
    )
    refreshed_context = service.get_authenticated_session_context(signup_result.session_token)
    assert refreshed_context is not None

    with pytest.raises(TwoFactorAlreadyEnabledError):
        service.enable_two_factor(
            context=refreshed_context,
            code=_totp_code(service, context.account_id),
            client_info=_client_info(),
        )


def test_session_listing_and_revocation_behaviors() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="device-user",
        email="device@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    current_context = service.get_authenticated_session_context(signup_result.session_token)
    assert current_context is not None
    second_login = service.login(
        email="device@example.com",
        password="Password123",
        client_info=AuthClientInfo(ip_address="10.0.0.2", user_agent="other-device"),
    )
    second_context = service.get_authenticated_session_context(second_login.session_token)
    assert second_context is not None

    sessions_before = service.list_active_sessions(context=current_context)
    assert len(sessions_before) == 2
    assert any(session_item.is_current for session_item in sessions_before)

    service.revoke_other_sessions(context=current_context, client_info=_client_info())
    sessions_after = service.list_active_sessions(context=current_context)
    assert len(sessions_after) == 1
    assert sessions_after[0].session_id == current_context.session_id
    assert service.get_authenticated_session_context(second_login.session_token) is None

    with pytest.raises(SessionNotFoundError):
        service.revoke_session_by_id(
            context=current_context,
            session_id=second_context.session_id,
            client_info=_client_info(),
        )


def test_account_closure_revokes_sessions_and_blocks_future_login() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="close-user",
        email="close@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    current_context = service.get_authenticated_session_context(signup_result.session_token)
    assert current_context is not None
    service.login(
        email="close@example.com",
        password="Password123",
        client_info=AuthClientInfo(ip_address="10.0.0.3", user_agent="tablet"),
    )

    service.close_account(
        context=current_context,
        current_password="Password123",
        code=None,
        recovery_code=None,
        client_info=_client_info(),
    )

    account = session.scalar(select(Account).where(Account.email == "close@example.com"))
    persisted_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == current_context.account_id)
    ).all()
    assert account is not None
    assert account.status == "closed"
    assert all(persisted_session.revoked_at is not None for persisted_session in persisted_sessions)
    assert service.get_authenticated_session_context(signup_result.session_token) is None

    with pytest.raises(AccountAccessRestrictedError) as exc:
        service.login(
            email="close@example.com",
            password="Password123",
            client_info=_client_info(),
        )

    assert exc.value.status == "closed"


def test_cleanup_stale_sessions_deletes_expired_and_revoked_rows_only() -> None:
    session = _create_in_memory_session()
    service = _build_service(session)
    signup_result = service.signup(
        username="cleanup-user",
        email="cleanup@example.com",
        password="Password123",
        client_info=_client_info(),
    )
    current_context = service.get_authenticated_session_context(signup_result.session_token)
    assert current_context is not None

    second_login = service.login(
        email="cleanup@example.com",
        password="Password123",
        client_info=AuthClientInfo(ip_address="10.0.0.20", user_agent="cleanup-other"),
    )
    second_context = service.get_authenticated_session_context(second_login.session_token)
    assert second_context is not None
    third_login = service.login(
        email="cleanup@example.com",
        password="Password123",
        client_info=AuthClientInfo(ip_address="10.0.0.21", user_agent="cleanup-active"),
    )
    third_context = service.get_authenticated_session_context(third_login.session_token)
    assert third_context is not None

    sessions_before = session.scalars(
        select(AuthSession).where(AuthSession.account_id == current_context.account_id)
    ).all()
    assert len(sessions_before) == 3

    sessions_by_id = {persisted_session.id: persisted_session for persisted_session in sessions_before}
    sessions_by_id[current_context.session_id].expires_at = datetime(
        2026, 4, 18, 12, 0, tzinfo=timezone.utc
    )
    sessions_by_id[second_context.session_id].revoked_at = datetime(
        2026, 4, 19, 12, 0, tzinfo=timezone.utc
    )
    session.commit()

    result = service.cleanup_stale_sessions(
        stale_before=datetime(2026, 4, 19, 13, 0, tzinfo=timezone.utc)
    )

    remaining_sessions = session.scalars(
        select(AuthSession).where(AuthSession.account_id == current_context.account_id)
    ).all()

    assert result.deleted_session_count == 2
    assert [persisted_session.id for persisted_session in remaining_sessions] == [third_context.session_id]
