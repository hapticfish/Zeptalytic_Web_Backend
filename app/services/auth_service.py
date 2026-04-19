from __future__ import annotations

import hashlib
import hmac
import secrets
from base64 import b32decode, b32encode
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import quote
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.repositories.auth_repository import (
    AuthRepository,
    AuthSessionAccountRecord,
    EmailVerificationTokenRecord,
    PasswordResetTokenRecord,
    SessionDeviceRecord,
    TwoFactorSettingsRecord,
)


@dataclass(slots=True)
class AuthenticatedSessionContext:
    session_id: UUID
    account_id: UUID
    username: str
    email: str
    status: str
    role: str
    email_verified_at: datetime | None
    session_created_at: datetime
    session_expires_at: datetime
    session_revoked_at: datetime | None
    ip_address: str | None
    user_agent: str | None
    two_factor_enabled: bool
    two_factor_method: str | None
    recovery_methods_available_count: int
    recovery_codes_generated_at: datetime | None

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None


@dataclass(slots=True)
class AuthClientInfo:
    ip_address: str | None
    user_agent: str | None


@dataclass(slots=True)
class AuthMutationResult:
    session_token: str
    context: AuthenticatedSessionContext


@dataclass(slots=True)
class TwoFactorEnrollment:
    secret: str
    otpauth_uri: str


@dataclass(slots=True)
class SessionDevice:
    session_id: UUID
    created_at: datetime
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None
    is_current: bool


@dataclass(slots=True)
class StaleSessionCleanupResult:
    deleted_session_count: int
    stale_before: datetime


class AuthenticationRequiredError(Exception):
    """Raised when a request does not present a valid authenticated session."""


class EmailVerificationRequiredError(Exception):
    """Raised when an account is authenticated but still pending verification."""


class AccountAccessRestrictedError(Exception):
    """Raised when an account lifecycle state blocks the requested action."""

    def __init__(self, status: str) -> None:
        super().__init__(f"Account access is restricted for status {status}.")
        self.status = status


class DuplicateAccountError(Exception):
    """Raised when a signup request conflicts with an existing account."""

    def __init__(self, conflicts: list[str]) -> None:
        super().__init__("Account already exists.")
        self.conflicts = conflicts


class InvalidCredentialsError(Exception):
    """Raised when an auth request presents invalid credentials."""


class EmailVerificationTokenInvalidError(Exception):
    """Raised when an email-verification token cannot be used."""

    def __init__(self, reason: str) -> None:
        super().__init__("Email verification token is invalid.")
        self.reason = reason


class PasswordResetTokenInvalidError(Exception):
    """Raised when a password-reset token cannot be used."""

    def __init__(self, reason: str) -> None:
        super().__init__("Password reset token is invalid.")
        self.reason = reason


class CurrentPasswordInvalidError(Exception):
    """Raised when an authenticated password change has an invalid current password."""


class TwoFactorNotEnabledError(Exception):
    """Raised when 2FA operations require an enabled 2FA configuration."""


class TwoFactorAlreadyEnabledError(Exception):
    """Raised when an account attempts to re-enable 2FA without disabling it first."""


class TwoFactorCodeInvalidError(Exception):
    """Raised when a TOTP or recovery code cannot be validated."""

    def __init__(self, reason: str) -> None:
        super().__init__("Two-factor code is invalid.")
        self.reason = reason


class SessionNotFoundError(Exception):
    """Raised when a requested active session does not exist for the account."""


class ParentAccountLinker(Protocol):
    def ensure_account_link(self, account_id: UUID) -> None: ...


class NoOpParentAccountLinker:
    def ensure_account_link(self, account_id: UUID) -> None:
        del account_id


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        db: Session,
        *,
        session_ttl_hours: int = 24 * 30,
        email_verification_ttl_hours: int = 24,
        password_reset_ttl_hours: int = 2,
        totp_issuer: str = "Zeptalytic",
        totp_secret_key: str = "dev-insecure-change-me",
        parent_account_linker: ParentAccountLinker | None = None,
    ) -> None:
        self._repository = repository
        self._db = db
        self._session_ttl = timedelta(hours=session_ttl_hours)
        self._email_verification_ttl = timedelta(hours=email_verification_ttl_hours)
        self._password_reset_ttl = timedelta(hours=password_reset_ttl_hours)
        self._totp_issuer = totp_issuer
        self._totp_secret_key = totp_secret_key
        self._parent_account_linker = parent_account_linker or NoOpParentAccountLinker()

    def get_authenticated_session_context(
        self,
        session_token: str | None,
    ) -> AuthenticatedSessionContext | None:
        if not session_token:
            return None

        session_record = self._repository.get_session_account_by_token_hash(
            self._hash_session_token(session_token)
        )
        if session_record is None:
            return None

        if session_record.session_revoked_at is not None:
            return None

        session_expires_at = self._ensure_aware_utc(session_record.session_expires_at)
        if session_expires_at is not None and session_expires_at <= datetime.now(timezone.utc):
            return None

        return self._build_context(session_record)

    @staticmethod
    def ensure_account_status_allows_authenticated_access(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        if context.status == "closed":
            raise AccountAccessRestrictedError(context.status)
        return context

    @staticmethod
    def ensure_email_verified(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        if context.status == "pending_verification" or not context.is_email_verified:
            raise EmailVerificationRequiredError("Email verification is required.")
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        AuthService.ensure_account_status_allows_authenticated_access(context)
        if context.status == "suspended":
            raise AccountAccessRestrictedError(context.status)
        return context

    def signup(
        self,
        *,
        username: str,
        email: str,
        password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        conflicts = self._get_signup_conflicts(
            username=normalized_username,
            email=normalized_email,
        )
        if conflicts:
            raise DuplicateAccountError(conflicts)

        now = datetime.now(timezone.utc)
        password_hash = self._hash_password(password)
        verification_token = self._generate_token()
        session_token = self._generate_token()

        try:
            account = self._repository.create_account(
                username=normalized_username,
                email=normalized_email,
                password_hash=password_hash,
                status="pending_verification",
                role="user",
            )
            self._parent_account_linker.ensure_account_link(account.id)
            self._repository.create_profile(account_id=account.id, display_name=account.username)
            self._repository.create_profile_preferences(account_id=account.id)
            self._repository.create_communication_preferences(account_id=account.id)
            security_settings = self._repository.create_account_security_settings(account_id=account.id)
            self._repository.create_email_verification_token(
                account_id=account.id,
                token_hash=self._hash_secret(verification_token),
                expires_at=now + self._email_verification_ttl,
            )
            auth_session = self._repository.create_auth_session(
                account_id=account.id,
                session_token_hash=self._hash_session_token(session_token),
                expires_at=now + self._session_ttl,
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
            )
            self._repository.update_account_last_login(account_id=account.id, last_login_at=now)
            self._repository.record_auth_event(
                account_id=account.id,
                event_type="signup_success",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": account.status},
            )
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise DuplicateAccountError(
                self._get_signup_conflicts(username=normalized_username, email=normalized_email)
                or ["email_or_username"]
            ) from exc
        except Exception:
            self._db.rollback()
            raise

        return AuthMutationResult(
            session_token=session_token,
            context=self._build_context(
                self._repository.build_session_account_record(
                    account=account,
                    auth_session=auth_session,
                    security_settings=security_settings,
                )
            ),
        )

    def login(
        self,
        *,
        email: str,
        password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        normalized_email = email.strip().lower()
        account = self._repository.get_account_by_email(normalized_email)
        if account is None:
            raise InvalidCredentialsError("Invalid credentials.")

        if not self._verify_password(password, account.password_hash):
            self._repository.record_auth_event(
                account_id=account.id,
                event_type="login_failed_invalid_credentials",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": account.status},
            )
            self._db.commit()
            raise InvalidCredentialsError("Invalid credentials.")

        if account.status == "closed":
            self._repository.record_auth_event(
                account_id=account.id,
                event_type="login_failed_account_closed",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": account.status},
            )
            self._db.commit()
            raise AccountAccessRestrictedError(account.status)

        now = datetime.now(timezone.utc)
        session_token = self._generate_token()
        security_settings = self._repository.get_two_factor_settings(account_id=account.id)
        try:
            auth_session = self._repository.create_auth_session(
                account_id=account.id,
                session_token_hash=self._hash_session_token(session_token),
                expires_at=now + self._session_ttl,
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
            )
            self._repository.update_account_last_login(account_id=account.id, last_login_at=now)
            self._repository.record_auth_event(
                account_id=account.id,
                event_type="login_success",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": account.status},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return AuthMutationResult(
            session_token=session_token,
            context=self._build_context(
                self._repository.build_session_account_record(
                    account=account,
                    auth_session=auth_session,
                    security_settings=None if security_settings is None else account_security_settings_record_to_model(
                        security_settings
                    ),
                )
            ),
        )

    def verify_email(
        self,
        *,
        token: str,
        client_info: AuthClientInfo,
    ) -> None:
        token_record = self._get_verification_token_record(token)
        now = datetime.now(timezone.utc)

        try:
            self._repository.mark_email_verification_token_used(
                token_id=token_record.token_id,
                used_at=now,
            )
            if token_record.email_verified_at is None:
                self._repository.mark_account_email_verified(
                    account_id=token_record.account_id,
                    verified_at=now,
                    activate_pending_account=token_record.account_status == "pending_verification",
                )
            self._repository.record_auth_event(
                account_id=token_record.account_id,
                event_type="email_verification_completed",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"previous_status": token_record.account_status},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def resend_email_verification(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
    ) -> None:
        if context.is_email_verified:
            return

        now = datetime.now(timezone.utc)
        try:
            self._repository.create_email_verification_token(
                account_id=context.account_id,
                token_hash=self._hash_secret(self._generate_token()),
                expires_at=now + self._email_verification_ttl,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="email_verification_resent",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": context.status},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def logout(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
        revoke_all_sessions: bool = False,
    ) -> None:
        revoked_at = datetime.now(timezone.utc)
        try:
            self._repository.revoke_session(session_id=context.session_id, revoked_at=revoked_at)
            if revoke_all_sessions:
                self._repository.revoke_other_sessions(
                    account_id=context.account_id,
                    excluded_session_id=context.session_id,
                    revoked_at=revoked_at,
                )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="logout_success",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"revoke_all_sessions": revoke_all_sessions},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def forgot_password(
        self,
        *,
        email: str,
        client_info: AuthClientInfo,
    ) -> None:
        normalized_email = email.strip().lower()
        account = self._repository.get_account_by_email(normalized_email)
        if account is None or account.status == "closed":
            return

        now = datetime.now(timezone.utc)
        try:
            self._repository.create_password_reset_token(
                account_id=account.id,
                token_hash=self._hash_secret(self._generate_token()),
                expires_at=now + self._password_reset_ttl,
            )
            self._repository.record_auth_event(
                account_id=account.id,
                event_type="password_reset_requested",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": account.status},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        client_info: AuthClientInfo,
    ) -> None:
        token_record = self._get_password_reset_token_record(token)
        now = datetime.now(timezone.utc)

        try:
            self._repository.mark_password_reset_token_used(
                token_id=token_record.token_id,
                used_at=now,
            )
            self._repository.update_account_password_hash(
                account_id=token_record.account_id,
                password_hash=self._hash_password(new_password),
            )
            self._repository.revoke_all_sessions(
                account_id=token_record.account_id,
                revoked_at=now,
            )
            self._repository.record_auth_event(
                account_id=token_record.account_id,
                event_type="password_reset_completed",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"account_status": token_record.account_status},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def change_password(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        new_password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        account = self._repository.get_account_by_email(context.email)
        if account is None or not self._verify_password(current_password, account.password_hash):
            raise CurrentPasswordInvalidError("Current password is invalid.")

        now = datetime.now(timezone.utc)
        session_token = self._generate_token()
        security_settings = self._repository.get_two_factor_settings(account_id=context.account_id)
        try:
            self._repository.update_account_password_hash(
                account_id=context.account_id,
                password_hash=self._hash_password(new_password),
            )
            self._repository.revoke_all_sessions(
                account_id=context.account_id,
                revoked_at=now,
            )
            auth_session = self._repository.create_auth_session(
                account_id=context.account_id,
                session_token_hash=self._hash_session_token(session_token),
                expires_at=now + self._session_ttl,
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="password_change_completed",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"rotated_session": True},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return AuthMutationResult(
            session_token=session_token,
            context=self._build_context(
                self._repository.build_session_account_record(
                    account=account,
                    auth_session=auth_session,
                    security_settings=None if security_settings is None else account_security_settings_record_to_model(
                        security_settings
                    ),
                )
            ),
        )

    def begin_two_factor_enrollment(
        self,
        *,
        context: AuthenticatedSessionContext,
    ) -> TwoFactorEnrollment:
        settings = self._get_two_factor_settings(context.account_id)
        if settings.two_factor_enabled:
            raise TwoFactorAlreadyEnabledError("Two-factor authentication is already enabled.")
        secret = self._derive_totp_secret(context.account_id)
        label = quote(f"{self._totp_issuer}:{settings.email}")
        issuer = quote(self._totp_issuer)
        return TwoFactorEnrollment(
            secret=secret,
            otpauth_uri=f"otpauth://totp/{label}?secret={secret}&issuer={issuer}",
        )

    def enable_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        code: str,
        client_info: AuthClientInfo,
    ) -> list[str]:
        settings = self._get_two_factor_settings(context.account_id)
        if settings.two_factor_enabled:
            raise TwoFactorAlreadyEnabledError("Two-factor authentication is already enabled.")
        if not self._verify_totp_code(account_id=context.account_id, code=code):
            raise TwoFactorCodeInvalidError("invalid")

        recovery_codes = self._generate_recovery_codes()
        now = datetime.now(timezone.utc)
        try:
            self._repository.replace_recovery_codes(
                account_id=context.account_id,
                code_hashes=[self._hash_secret(recovery_code) for recovery_code in recovery_codes],
            )
            self._repository.set_two_factor_state(
                account_id=context.account_id,
                enabled=True,
                method="totp",
                recovery_methods_available_count=len(recovery_codes),
                recovery_codes_generated_at=now,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="two_factor_enabled",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"recovery_code_count": len(recovery_codes)},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return recovery_codes

    def challenge_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        try:
            self._assert_two_factor_challenge(
                account_id=context.account_id,
                code=code,
                recovery_code=recovery_code,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="two_factor_challenge_succeeded",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"used_recovery_code": recovery_code is not None},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def regenerate_recovery_codes(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> list[str]:
        settings = self._get_two_factor_settings(context.account_id)
        if not settings.two_factor_enabled:
            raise TwoFactorNotEnabledError("Two-factor authentication is not enabled.")
        self._require_current_password(settings=settings, current_password=current_password)
        self._assert_two_factor_challenge(
            account_id=context.account_id,
            code=code,
            recovery_code=recovery_code,
        )

        recovery_codes = self._generate_recovery_codes()
        now = datetime.now(timezone.utc)
        try:
            self._repository.replace_recovery_codes(
                account_id=context.account_id,
                code_hashes=[self._hash_secret(recovery_code_value) for recovery_code_value in recovery_codes],
            )
            self._repository.set_two_factor_state(
                account_id=context.account_id,
                enabled=True,
                method="totp",
                recovery_methods_available_count=len(recovery_codes),
                recovery_codes_generated_at=now,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="two_factor_recovery_codes_regenerated",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"recovery_code_count": len(recovery_codes)},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return recovery_codes

    def disable_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        settings = self._get_two_factor_settings(context.account_id)
        if not settings.two_factor_enabled:
            raise TwoFactorNotEnabledError("Two-factor authentication is not enabled.")
        self._require_current_password(settings=settings, current_password=current_password)
        self._assert_two_factor_challenge(
            account_id=context.account_id,
            code=code,
            recovery_code=recovery_code,
        )

        try:
            self._repository.replace_recovery_codes(account_id=context.account_id, code_hashes=[])
            self._repository.set_two_factor_state(
                account_id=context.account_id,
                enabled=False,
                method=None,
                recovery_methods_available_count=0,
                recovery_codes_generated_at=None,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="two_factor_disabled",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def list_active_sessions(
        self,
        *,
        context: AuthenticatedSessionContext,
    ) -> list[SessionDevice]:
        return [
            self._build_session_device(session_record, current_session_id=context.session_id)
            for session_record in self._repository.list_active_sessions_for_account(
                account_id=context.account_id
            )
        ]

    def revoke_session_by_id(
        self,
        *,
        context: AuthenticatedSessionContext,
        session_id: UUID,
        client_info: AuthClientInfo,
    ) -> bool:
        session_record = self._repository.get_active_session_for_account(
            account_id=context.account_id,
            session_id=session_id,
        )
        if session_record is None:
            raise SessionNotFoundError("Session not found.")

        revoked_at = datetime.now(timezone.utc)
        try:
            self._repository.revoke_session(session_id=session_id, revoked_at=revoked_at)
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="session_revoked",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"revoked_session_id": str(session_id)},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return session_id == context.session_id

    def revoke_other_sessions(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
    ) -> None:
        revoked_at = datetime.now(timezone.utc)
        try:
            self._repository.revoke_other_sessions(
                account_id=context.account_id,
                excluded_session_id=context.session_id,
                revoked_at=revoked_at,
            )
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="other_sessions_revoked",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def close_account(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        settings = self._get_two_factor_settings(context.account_id)
        self._require_current_password(settings=settings, current_password=current_password)
        if settings.two_factor_enabled:
            self._assert_two_factor_challenge(
                account_id=context.account_id,
                code=code,
                recovery_code=recovery_code,
            )

        revoked_at = datetime.now(timezone.utc)
        try:
            self._repository.update_account_status(account_id=context.account_id, status="closed")
            self._repository.revoke_all_sessions(account_id=context.account_id, revoked_at=revoked_at)
            self._repository.record_auth_event(
                account_id=context.account_id,
                event_type="account_closed",
                ip_address=client_info.ip_address,
                user_agent=client_info.user_agent,
                event_metadata={"had_two_factor_enabled": settings.two_factor_enabled},
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    def cleanup_stale_sessions(
        self,
        *,
        stale_before: datetime | None = None,
    ) -> StaleSessionCleanupResult:
        cutoff = stale_before or datetime.now(timezone.utc)
        try:
            deleted_session_count = self._repository.delete_stale_sessions(stale_before=cutoff)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return StaleSessionCleanupResult(
            deleted_session_count=deleted_session_count,
            stale_before=cutoff,
        )

    def _get_signup_conflicts(self, *, username: str, email: str) -> list[str]:
        conflicts: list[str] = []
        if self._repository.get_account_by_username(username) is not None:
            conflicts.append("username")
        if self._repository.get_account_by_email(email) is not None:
            conflicts.append("email")
        return conflicts

    def _get_verification_token_record(self, token: str) -> EmailVerificationTokenRecord:
        token_record = self._repository.get_email_verification_token_record_by_token_hash(
            self._hash_secret(token)
        )
        if token_record is None:
            raise EmailVerificationTokenInvalidError("invalid")

        now = datetime.now(timezone.utc)
        expires_at = self._ensure_aware_utc(token_record.expires_at)
        used_at = self._ensure_aware_utc(token_record.used_at)
        if used_at is not None:
            raise EmailVerificationTokenInvalidError("used")
        if expires_at is not None and expires_at <= now:
            raise EmailVerificationTokenInvalidError("expired")
        return token_record

    def _get_password_reset_token_record(self, token: str) -> PasswordResetTokenRecord:
        token_record = self._repository.get_password_reset_token_record_by_token_hash(
            self._hash_secret(token)
        )
        if token_record is None:
            raise PasswordResetTokenInvalidError("invalid")

        now = datetime.now(timezone.utc)
        expires_at = self._ensure_aware_utc(token_record.expires_at)
        used_at = self._ensure_aware_utc(token_record.used_at)
        if used_at is not None:
            raise PasswordResetTokenInvalidError("used")
        if expires_at is not None and expires_at <= now:
            raise PasswordResetTokenInvalidError("expired")
        if token_record.account_status == "closed":
            raise PasswordResetTokenInvalidError("account_closed")
        return token_record

    def _get_two_factor_settings(self, account_id: UUID) -> TwoFactorSettingsRecord:
        settings = self._repository.get_two_factor_settings(account_id=account_id)
        if settings is None:
            raise AuthenticationRequiredError("Authentication is required.")
        return settings

    def _require_current_password(
        self,
        *,
        settings: TwoFactorSettingsRecord,
        current_password: str,
    ) -> None:
        if not self._verify_password(current_password, settings.password_hash):
            raise CurrentPasswordInvalidError("Current password is invalid.")

    def _assert_two_factor_challenge(
        self,
        *,
        account_id: UUID,
        code: str | None,
        recovery_code: str | None,
    ) -> None:
        settings = self._get_two_factor_settings(account_id)
        if not settings.two_factor_enabled:
            raise TwoFactorNotEnabledError("Two-factor authentication is not enabled.")
        if code:
            if self._verify_totp_code(account_id=account_id, code=code):
                return
            raise TwoFactorCodeInvalidError("invalid")
        if recovery_code:
            self._consume_recovery_code(account_id=account_id, recovery_code=recovery_code)
            return
        raise TwoFactorCodeInvalidError("missing")

    def _consume_recovery_code(self, *, account_id: UUID, recovery_code: str) -> None:
        recovery_code_hash = self._hash_secret(recovery_code)
        recovery_codes = self._repository.list_recovery_codes(account_id=account_id)
        matching_code = next(
            (
                code_record
                for code_record in recovery_codes
                if hmac.compare_digest(code_record.code_hash, recovery_code_hash)
            ),
            None,
        )
        if matching_code is None:
            raise TwoFactorCodeInvalidError("invalid")
        if matching_code.used_at is not None:
            raise TwoFactorCodeInvalidError("used")

        used_at = datetime.now(timezone.utc)
        remaining_codes = max(
            0,
            sum(1 for code_record in recovery_codes if code_record.used_at is None) - 1,
        )
        self._repository.mark_recovery_code_used(
            recovery_code_id=matching_code.recovery_code_id,
            used_at=used_at,
        )
        settings = self._get_two_factor_settings(account_id)
        self._repository.set_two_factor_state(
            account_id=account_id,
            enabled=settings.two_factor_enabled,
            method=settings.two_factor_method,
            recovery_methods_available_count=remaining_codes,
            recovery_codes_generated_at=settings.recovery_codes_generated_at,
        )

    def _derive_totp_secret(self, account_id: UUID) -> str:
        digest = hmac.new(
            self._totp_secret_key.encode("utf-8"),
            account_id.hex.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return b32encode(digest[:20]).decode("ascii").rstrip("=")

    def _verify_totp_code(self, *, account_id: UUID, code: str) -> bool:
        normalized_code = code.strip().replace(" ", "")
        if not normalized_code.isdigit() or len(normalized_code) != 6:
            return False
        secret = self._derive_totp_secret(account_id)
        current_counter = int(datetime.now(timezone.utc).timestamp() // 30)
        for offset in (-1, 0, 1):
            if self._generate_totp_code(secret=secret, counter=current_counter + offset) == normalized_code:
                return True
        return False

    @staticmethod
    def _generate_totp_code(*, secret: str, counter: int) -> str:
        normalized_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
        key = b32decode(normalized_secret, casefold=True)
        counter_bytes = counter.to_bytes(8, byteorder="big", signed=False)
        digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        binary = int.from_bytes(digest[offset : offset + 4], byteorder="big") & 0x7FFFFFFF
        return f"{binary % 1_000_000:06d}"

    @staticmethod
    def _generate_recovery_codes(count: int = 8) -> list[str]:
        return [
            f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
            for _ in range(count)
        ]

    @staticmethod
    def _build_session_device(
        session_record: SessionDeviceRecord,
        *,
        current_session_id: UUID,
    ) -> SessionDevice:
        return SessionDevice(
            session_id=session_record.session_id,
            created_at=AuthService._ensure_aware_utc(session_record.created_at),
            expires_at=AuthService._ensure_aware_utc(session_record.expires_at),
            ip_address=session_record.ip_address,
            user_agent=session_record.user_agent,
            is_current=session_record.session_id == current_session_id,
        )

    @staticmethod
    def _hash_session_token(session_token: str) -> str:
        return hashlib.sha256(session_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        iterations = 600_000
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return f"pbkdf2_sha256${iterations}${salt}${digest}"

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        parts = stored_hash.split("$", maxsplit=3)
        if len(parts) != 4:
            return False
        algorithm, iterations, salt, digest = parts
        if algorithm != "pbkdf2_sha256":
            return False
        candidate_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate_digest, digest)

    @staticmethod
    def _build_context(
        session_record: AuthSessionAccountRecord,
    ) -> AuthenticatedSessionContext:
        return AuthenticatedSessionContext(
            session_id=session_record.session_id,
            account_id=session_record.account_id,
            username=session_record.username,
            email=session_record.email,
            status=session_record.status,
            role=session_record.role,
            email_verified_at=AuthService._ensure_aware_utc(session_record.email_verified_at),
            session_created_at=AuthService._ensure_aware_utc(session_record.session_created_at),
            session_expires_at=AuthService._ensure_aware_utc(session_record.session_expires_at),
            session_revoked_at=AuthService._ensure_aware_utc(session_record.session_revoked_at),
            ip_address=session_record.ip_address,
            user_agent=session_record.user_agent,
            two_factor_enabled=session_record.two_factor_enabled,
            two_factor_method=session_record.two_factor_method,
            recovery_methods_available_count=session_record.recovery_methods_available_count,
            recovery_codes_generated_at=AuthService._ensure_aware_utc(
                session_record.recovery_codes_generated_at
            ),
        )

    @staticmethod
    def _ensure_aware_utc(value: datetime | None) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=timezone.utc)


def build_auth_service(db: Session) -> AuthService:
    from app.core.config import settings

    return AuthService(
        AuthRepository(db),
        db,
        session_ttl_hours=settings.auth_session_ttl_hours,
        email_verification_ttl_hours=settings.auth_email_verification_ttl_hours,
        password_reset_ttl_hours=settings.auth_password_reset_ttl_hours,
        totp_issuer=settings.auth_totp_issuer,
        totp_secret_key=settings.auth_totp_secret_key,
    )


def account_security_settings_record_to_model(
    settings: TwoFactorSettingsRecord,
):
    from app.db.models.account_security_settings import AccountSecuritySettings

    return AccountSecuritySettings(
        account_id=settings.account_id,
        two_factor_enabled=settings.two_factor_enabled,
        two_factor_method=settings.two_factor_method,
        recovery_methods_available_count=settings.recovery_methods_available_count,
        recovery_codes_generated_at=settings.recovery_codes_generated_at,
    )
