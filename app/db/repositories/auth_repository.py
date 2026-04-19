from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
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


@dataclass(slots=True)
class AuthSessionAccountRecord:
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


@dataclass(slots=True)
class EmailVerificationTokenRecord:
    token_id: UUID
    account_id: UUID
    account_status: str
    email_verified_at: datetime | None
    expires_at: datetime
    used_at: datetime | None


@dataclass(slots=True)
class PasswordResetTokenRecord:
    token_id: UUID
    account_id: UUID
    account_status: str
    password_hash: str
    expires_at: datetime
    used_at: datetime | None


@dataclass(slots=True)
class TwoFactorSettingsRecord:
    account_id: UUID
    email: str
    password_hash: str
    two_factor_enabled: bool
    two_factor_method: str | None
    recovery_methods_available_count: int
    recovery_codes_generated_at: datetime | None


@dataclass(slots=True)
class RecoveryCodeRecord:
    recovery_code_id: UUID
    code_hash: str
    used_at: datetime | None


@dataclass(slots=True)
class SessionDeviceRecord:
    session_id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    ip_address: str | None
    user_agent: str | None


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_account_by_email(self, email: str) -> Account | None:
        return self._db.scalar(select(Account).where(Account.email == email))

    def get_account_by_username(self, username: str) -> Account | None:
        return self._db.scalar(select(Account).where(Account.username == username))

    def get_session_account_by_token_hash(
        self,
        session_token_hash: str,
    ) -> AuthSessionAccountRecord | None:
        row = self._db.execute(
            select(AuthSession, Account, AccountSecuritySettings)
            .join(Account, Account.id == AuthSession.account_id)
            .join(AccountSecuritySettings, AccountSecuritySettings.account_id == Account.id)
            .where(AuthSession.session_token_hash == session_token_hash)
        ).one_or_none()
        if row is None:
            return None

        auth_session, account, security_settings = row
        return AuthSessionAccountRecord(
            session_id=auth_session.id,
            account_id=account.id,
            username=account.username,
            email=account.email,
            status=account.status,
            role=account.role,
            email_verified_at=account.email_verified_at,
            session_created_at=auth_session.created_at,
            session_expires_at=auth_session.expires_at,
            session_revoked_at=auth_session.revoked_at,
            ip_address=auth_session.ip_address,
            user_agent=auth_session.user_agent,
            two_factor_enabled=security_settings.two_factor_enabled,
            two_factor_method=security_settings.two_factor_method,
            recovery_methods_available_count=security_settings.recovery_methods_available_count,
            recovery_codes_generated_at=security_settings.recovery_codes_generated_at,
        )

    def create_account(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
        status: str,
        role: str,
    ) -> Account:
        account = Account(
            username=username,
            email=email,
            password_hash=password_hash,
            status=status,
            role=role,
        )
        self._db.add(account)
        self._db.flush()
        return account

    def create_profile(self, *, account_id: UUID, display_name: str) -> Profile:
        profile = Profile(account_id=account_id, display_name=display_name)
        self._db.add(profile)
        self._db.flush()
        return profile

    def create_profile_preferences(self, *, account_id: UUID) -> ProfilePreference:
        preferences = ProfilePreference(account_id=account_id)
        self._db.add(preferences)
        self._db.flush()
        return preferences

    def create_communication_preferences(self, *, account_id: UUID) -> CommunicationPreference:
        preferences = CommunicationPreference(account_id=account_id)
        self._db.add(preferences)
        self._db.flush()
        return preferences

    def create_account_security_settings(self, *, account_id: UUID) -> AccountSecuritySettings:
        security_settings = AccountSecuritySettings(account_id=account_id)
        self._db.add(security_settings)
        self._db.flush()
        return security_settings

    def get_two_factor_settings(self, *, account_id: UUID) -> TwoFactorSettingsRecord | None:
        row = self._db.execute(
            select(Account, AccountSecuritySettings)
            .join(AccountSecuritySettings, AccountSecuritySettings.account_id == Account.id)
            .where(Account.id == account_id)
        ).one_or_none()
        if row is None:
            return None

        account, settings = row
        return TwoFactorSettingsRecord(
            account_id=account.id,
            email=account.email,
            password_hash=account.password_hash,
            two_factor_enabled=settings.two_factor_enabled,
            two_factor_method=settings.two_factor_method,
            recovery_methods_available_count=settings.recovery_methods_available_count,
            recovery_codes_generated_at=settings.recovery_codes_generated_at,
        )

    def set_two_factor_state(
        self,
        *,
        account_id: UUID,
        enabled: bool,
        method: str | None,
        recovery_methods_available_count: int,
        recovery_codes_generated_at: datetime | None,
    ) -> None:
        self._db.execute(
            update(AccountSecuritySettings)
            .where(AccountSecuritySettings.account_id == account_id)
            .values(
                two_factor_enabled=enabled,
                two_factor_method=method,
                recovery_methods_available_count=recovery_methods_available_count,
                recovery_codes_generated_at=recovery_codes_generated_at,
            )
        )

    def replace_recovery_codes(self, *, account_id: UUID, code_hashes: list[str]) -> None:
        self._db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.account_id == account_id))
        for code_hash in code_hashes:
            self._db.add(MfaRecoveryCode(account_id=account_id, code_hash=code_hash))
        self._db.flush()

    def list_recovery_codes(self, *, account_id: UUID) -> list[RecoveryCodeRecord]:
        recovery_codes = self._db.scalars(
            select(MfaRecoveryCode)
            .where(MfaRecoveryCode.account_id == account_id)
            .order_by(MfaRecoveryCode.created_at.asc(), MfaRecoveryCode.id.asc())
        ).all()
        return [
            RecoveryCodeRecord(
                recovery_code_id=recovery_code.id,
                code_hash=recovery_code.code_hash,
                used_at=recovery_code.used_at,
            )
            for recovery_code in recovery_codes
        ]

    def mark_recovery_code_used(self, *, recovery_code_id: UUID, used_at: datetime) -> None:
        self._db.execute(
            update(MfaRecoveryCode)
            .where(MfaRecoveryCode.id == recovery_code_id)
            .values(used_at=used_at)
        )

    def list_active_sessions_for_account(self, *, account_id: UUID) -> list[SessionDeviceRecord]:
        now = datetime.now(timezone.utc)
        sessions = self._db.scalars(
            select(AuthSession)
            .where(
                AuthSession.account_id == account_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .order_by(AuthSession.created_at.desc(), AuthSession.id.desc())
        ).all()
        return [
            SessionDeviceRecord(
                session_id=session.id,
                created_at=session.created_at,
                expires_at=session.expires_at,
                revoked_at=session.revoked_at,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
            )
            for session in sessions
        ]

    def get_active_session_for_account(
        self,
        *,
        account_id: UUID,
        session_id: UUID,
    ) -> SessionDeviceRecord | None:
        now = datetime.now(timezone.utc)
        session = self._db.scalar(
            select(AuthSession).where(
                AuthSession.account_id == account_id,
                AuthSession.id == session_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )
        if session is None:
            return None
        return SessionDeviceRecord(
            session_id=session.id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
        )

    def create_email_verification_token(
        self,
        *,
        account_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            account_id=account_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(token)
        self._db.flush()
        return token

    def get_email_verification_token_record_by_token_hash(
        self,
        token_hash: str,
    ) -> EmailVerificationTokenRecord | None:
        row = self._db.execute(
            select(EmailVerificationToken, Account)
            .join(Account, Account.id == EmailVerificationToken.account_id)
            .where(EmailVerificationToken.token_hash == token_hash)
        ).one_or_none()
        if row is None:
            return None

        token, account = row
        return EmailVerificationTokenRecord(
            token_id=token.id,
            account_id=account.id,
            account_status=account.status,
            email_verified_at=account.email_verified_at,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )

    def create_auth_session(
        self,
        *,
        account_id: UUID,
        session_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthSession:
        auth_session = AuthSession(
            account_id=account_id,
            session_token_hash=session_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._db.add(auth_session)
        self._db.flush()
        self._db.refresh(auth_session)
        return auth_session

    def create_password_reset_token(
        self,
        *,
        account_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            account_id=account_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(token)
        self._db.flush()
        return token

    def get_password_reset_token_record_by_token_hash(
        self,
        token_hash: str,
    ) -> PasswordResetTokenRecord | None:
        row = self._db.execute(
            select(PasswordResetToken, Account)
            .join(Account, Account.id == PasswordResetToken.account_id)
            .where(PasswordResetToken.token_hash == token_hash)
        ).one_or_none()
        if row is None:
            return None

        token, account = row
        return PasswordResetTokenRecord(
            token_id=token.id,
            account_id=account.id,
            account_status=account.status,
            password_hash=account.password_hash,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )

    def update_account_last_login(
        self,
        *,
        account_id: UUID,
        last_login_at: datetime,
    ) -> None:
        self._db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(last_login_at=last_login_at)
        )

    def mark_email_verification_token_used(
        self,
        *,
        token_id: UUID,
        used_at: datetime,
    ) -> None:
        self._db.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.id == token_id)
            .values(used_at=used_at)
        )

    def mark_account_email_verified(
        self,
        *,
        account_id: UUID,
        verified_at: datetime,
        activate_pending_account: bool,
    ) -> None:
        values: dict[str, object] = {"email_verified_at": verified_at}
        if activate_pending_account:
            values["status"] = "active"
        self._db.execute(update(Account).where(Account.id == account_id).values(**values))

    def revoke_session(self, *, session_id: UUID, revoked_at: datetime) -> None:
        self._db.execute(
            update(AuthSession)
            .where(AuthSession.id == session_id)
            .values(revoked_at=revoked_at)
        )

    def revoke_other_sessions(
        self,
        *,
        account_id: UUID,
        excluded_session_id: UUID,
        revoked_at: datetime,
    ) -> None:
        self._db.execute(
            update(AuthSession)
            .where(
                AuthSession.account_id == account_id,
                AuthSession.id != excluded_session_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

    def revoke_all_sessions(
        self,
        *,
        account_id: UUID,
        revoked_at: datetime,
    ) -> None:
        self._db.execute(
            update(AuthSession)
            .where(
                AuthSession.account_id == account_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

    def mark_password_reset_token_used(
        self,
        *,
        token_id: UUID,
        used_at: datetime,
    ) -> None:
        self._db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=used_at)
        )

    def update_account_password_hash(
        self,
        *,
        account_id: UUID,
        password_hash: str,
    ) -> None:
        self._db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(password_hash=password_hash)
        )

    def update_account_status(
        self,
        *,
        account_id: UUID,
        status: str,
    ) -> None:
        self._db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(status=status)
        )

    def record_auth_event(
        self,
        *,
        account_id: UUID,
        event_type: str,
        ip_address: str | None,
        user_agent: str | None,
        event_metadata: dict[str, object] | None = None,
    ) -> AuthEvent:
        auth_event = AuthEvent(
            account_id=account_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata or {},
        )
        self._db.add(auth_event)
        self._db.flush()
        return auth_event

    @staticmethod
    def build_session_account_record(
        *,
        account: Account,
        auth_session: AuthSession,
        security_settings: AccountSecuritySettings | None = None,
    ) -> AuthSessionAccountRecord:
        settings = security_settings or account_security_settings_fallback(account.id)
        return AuthSessionAccountRecord(
            session_id=auth_session.id,
            account_id=account.id,
            username=account.username,
            email=account.email,
            status=account.status,
            role=account.role,
            email_verified_at=account.email_verified_at,
            session_created_at=auth_session.created_at,
            session_expires_at=auth_session.expires_at,
            session_revoked_at=auth_session.revoked_at,
            ip_address=auth_session.ip_address,
            user_agent=auth_session.user_agent,
            two_factor_enabled=settings.two_factor_enabled,
            two_factor_method=settings.two_factor_method,
            recovery_methods_available_count=settings.recovery_methods_available_count,
            recovery_codes_generated_at=settings.recovery_codes_generated_at,
        )


def account_security_settings_fallback(account_id: UUID) -> AccountSecuritySettings:
    return AccountSecuritySettings(
        account_id=account_id,
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )
