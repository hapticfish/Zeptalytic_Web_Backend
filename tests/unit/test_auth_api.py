from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, require_normal_authenticated_session_context
from app.api.exception_handlers import register_exception_handlers
from app.main import app
from app.utils import register_request_id_middleware
from app.services.auth_service import (
    AccountAccessRestrictedError,
    AuthClientInfo,
    AuthMutationResult,
    AuthenticatedSessionContext,
    CurrentPasswordInvalidError,
    DuplicateAccountError,
    EmailVerificationRequiredError,
    EmailVerificationTokenInvalidError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
    SessionDevice,
    SessionNotFoundError,
    TwoFactorAlreadyEnabledError,
    TwoFactorCodeInvalidError,
    TwoFactorEnrollment,
    TwoFactorNotEnabledError,
)
from tests.unit.assertions import assert_standard_error_response


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context
        self.received_tokens: list[str | None] = []
        self.signup_calls: list[dict[str, object]] = []
        self.login_calls: list[dict[str, object]] = []
        self.logout_calls: list[dict[str, object]] = []
        self.verify_calls: list[dict[str, object]] = []
        self.resend_calls: list[dict[str, object]] = []
        self.forgot_password_calls: list[dict[str, object]] = []
        self.reset_password_calls: list[dict[str, object]] = []
        self.change_password_calls: list[dict[str, object]] = []
        self.enroll_two_factor_calls: list[dict[str, object]] = []
        self.verify_two_factor_calls: list[dict[str, object]] = []
        self.challenge_two_factor_calls: list[dict[str, object]] = []
        self.regenerate_recovery_code_calls: list[dict[str, object]] = []
        self.disable_two_factor_calls: list[dict[str, object]] = []
        self.list_session_calls: list[dict[str, object]] = []
        self.revoke_session_calls: list[dict[str, object]] = []
        self.revoke_other_sessions_calls: list[dict[str, object]] = []
        self.close_account_calls: list[dict[str, object]] = []

    def get_authenticated_session_context(
        self,
        session_token: str | None,
    ) -> AuthenticatedSessionContext | None:
        self.received_tokens.append(session_token)
        return self._context

    @staticmethod
    def ensure_account_status_allows_authenticated_access(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context

    @staticmethod
    def ensure_email_verified(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        if context.status == "pending_verification" or context.email_verified_at is None:
            raise EmailVerificationRequiredError("Email verification is required.")
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context

    def signup(
        self,
        *,
        username: str,
        email: str,
        password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        self.signup_calls.append(
            {
                "username": username,
                "email": email,
                "password": password,
                "client_info": client_info,
            }
        )
        if email == "duplicate@example.com":
            raise DuplicateAccountError(["email"])
        assert self._context is not None
        return AuthMutationResult(session_token="signup-token", context=self._context)

    def login(
        self,
        *,
        email: str,
        password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        self.login_calls.append(
            {
                "email": email,
                "password": password,
                "client_info": client_info,
            }
        )
        if password == "WrongPassword123":
            raise InvalidCredentialsError("Invalid credentials.")
        if email == "closed@example.com":
            raise AccountAccessRestrictedError("closed")
        assert self._context is not None
        return AuthMutationResult(session_token="login-token", context=self._context)

    def logout(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
        revoke_all_sessions: bool = False,
    ) -> None:
        self.logout_calls.append(
            {
                "context": context,
                "client_info": client_info,
                "revoke_all_sessions": revoke_all_sessions,
            }
        )

    def verify_email(
        self,
        *,
        token: str,
        client_info: AuthClientInfo,
    ) -> None:
        self.verify_calls.append({"token": token, "client_info": client_info})
        if token == "expired-token":
            raise EmailVerificationTokenInvalidError("expired")

    def resend_email_verification(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
    ) -> None:
        self.resend_calls.append({"context": context, "client_info": client_info})

    def forgot_password(
        self,
        *,
        email: str,
        client_info: AuthClientInfo,
    ) -> None:
        self.forgot_password_calls.append({"email": email, "client_info": client_info})

    def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        client_info: AuthClientInfo,
    ) -> None:
        self.reset_password_calls.append(
            {
                "token": token,
                "new_password": new_password,
                "client_info": client_info,
            }
        )
        if token == "expired-reset-token":
            raise PasswordResetTokenInvalidError("expired")

    def change_password(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        new_password: str,
        client_info: AuthClientInfo,
    ) -> AuthMutationResult:
        self.change_password_calls.append(
            {
                "context": context,
                "current_password": current_password,
                "new_password": new_password,
                "client_info": client_info,
            }
        )
        if current_password == "WrongPassword123":
            raise CurrentPasswordInvalidError("Current password is invalid.")
        assert self._context is not None
        return AuthMutationResult(session_token="changed-password-token", context=self._context)

    def begin_two_factor_enrollment(
        self,
        *,
        context: AuthenticatedSessionContext,
    ) -> TwoFactorEnrollment:
        self.enroll_two_factor_calls.append({"context": context})
        if context.two_factor_enabled:
            raise TwoFactorAlreadyEnabledError("Two-factor authentication is already enabled.")
        return TwoFactorEnrollment(
            secret="TESTSECRET",
            otpauth_uri="otpauth://totp/Zeptalytic:auth-user@example.com?secret=TESTSECRET&issuer=Zeptalytic",
        )

    def enable_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        code: str,
        client_info: AuthClientInfo,
    ) -> list[str]:
        self.verify_two_factor_calls.append(
            {"context": context, "code": code, "client_info": client_info}
        )
        if code == "000000":
            raise TwoFactorCodeInvalidError("invalid")
        return ["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"]

    def challenge_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        self.challenge_two_factor_calls.append(
            {
                "context": context,
                "code": code,
                "recovery_code": recovery_code,
                "client_info": client_info,
            }
        )
        if code == "000000" or recovery_code == "USED-CODE":
            raise TwoFactorCodeInvalidError("used" if recovery_code else "invalid")

    def regenerate_recovery_codes(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> list[str]:
        self.regenerate_recovery_code_calls.append(
            {
                "context": context,
                "current_password": current_password,
                "code": code,
                "recovery_code": recovery_code,
                "client_info": client_info,
            }
        )
        if current_password == "WrongPassword123":
            raise CurrentPasswordInvalidError("Current password is invalid.")
        return ["1111-2222-3333", "4444-5555-6666"]

    def disable_two_factor(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        self.disable_two_factor_calls.append(
            {
                "context": context,
                "current_password": current_password,
                "code": code,
                "recovery_code": recovery_code,
                "client_info": client_info,
            }
        )
        if not context.two_factor_enabled:
            raise TwoFactorNotEnabledError("Two-factor authentication is not enabled.")
        if current_password == "WrongPassword123":
            raise CurrentPasswordInvalidError("Current password is invalid.")

    def list_active_sessions(
        self,
        *,
        context: AuthenticatedSessionContext,
    ) -> list[SessionDevice]:
        self.list_session_calls.append({"context": context})
        return [
            SessionDevice(
                session_id=context.session_id,
                created_at=context.session_created_at,
                expires_at=context.session_expires_at,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                is_current=True,
            )
        ]

    def revoke_session_by_id(
        self,
        *,
        context: AuthenticatedSessionContext,
        session_id,
        client_info: AuthClientInfo,
    ) -> bool:
        self.revoke_session_calls.append(
            {"context": context, "session_id": session_id, "client_info": client_info}
        )
        if str(session_id).endswith("ffff"):
            raise SessionNotFoundError("Session not found.")
        return session_id == context.session_id

    def revoke_other_sessions(
        self,
        *,
        context: AuthenticatedSessionContext,
        client_info: AuthClientInfo,
    ) -> None:
        self.revoke_other_sessions_calls.append({"context": context, "client_info": client_info})

    def close_account(
        self,
        *,
        context: AuthenticatedSessionContext,
        current_password: str,
        code: str | None,
        recovery_code: str | None,
        client_info: AuthClientInfo,
    ) -> None:
        self.close_account_calls.append(
            {
                "context": context,
                "current_password": current_password,
                "code": code,
                "recovery_code": recovery_code,
                "client_info": client_info,
            }
        )
        if current_password == "WrongPassword123":
            raise CurrentPasswordInvalidError("Current password is invalid.")


def _build_context(
    *,
    status: str = "active",
    email_verified_at: datetime | None = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
    two_factor_enabled: bool = False,
    two_factor_method: str | None = None,
) -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="auth-user",
        email="auth-user@example.com",
        status=status,
        role="user",
        email_verified_at=email_verified_at,
        session_created_at=now - timedelta(hours=1),
        session_expires_at=now + timedelta(hours=1),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest-client",
        two_factor_enabled=two_factor_enabled,
        two_factor_method=two_factor_method,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


client = TestClient(app)


def test_auth_routes_are_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/auth/signup" in routes
    assert "/api/v1/auth/login" in routes
    assert "/api/v1/auth/verify-email" in routes
    assert "/api/v1/auth/resend-verification" in routes
    assert "/api/v1/auth/forgot-password" in routes
    assert "/api/v1/auth/reset-password" in routes
    assert "/api/v1/auth/change-password" in routes
    assert "/api/v1/auth/logout" in routes
    assert "/api/v1/auth/session" in routes
    assert "/api/v1/auth/2fa/enroll" in routes
    assert "/api/v1/auth/2fa/verify" in routes
    assert "/api/v1/auth/2fa/challenge" in routes
    assert "/api/v1/auth/2fa/recovery-codes/regenerate" in routes
    assert "/api/v1/auth/2fa/disable" in routes
    assert "/api/v1/auth/sessions" in routes
    assert "/api/v1/auth/sessions/{session_id}/revoke" in routes
    assert "/api/v1/auth/sessions/revoke-others" in routes
    assert "/api/v1/auth/account-closure" in routes


def test_auth_session_endpoint_returns_safe_session_contract() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "token-123")
        response = client.get("/api/v1/auth/session")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert stub_service.received_tokens == ["token-123"]
    assert payload["authenticated"] is True
    assert payload["account"] == {
        "account_id": str(stub_service._context.account_id),
        "username": "auth-user",
        "email": "auth-user@example.com",
        "status": "active",
        "role": "user",
        "email_verified_at": "2026-04-18T12:00:00Z",
    }
    assert payload["session"]["session_id"] == str(stub_service._context.session_id)
    assert payload["security"] == {
        "email_verification_required": False,
        "can_access_support": True,
        "can_access_billing": True,
        "can_access_normal_authenticated_routes": True,
        "can_access_product_launch": True,
        "two_factor_enabled": False,
        "two_factor_method": None,
        "recovery_methods_available_count": 0,
        "recovery_codes_generated_at": None,
    }


def test_auth_session_endpoint_requires_authenticated_cookie_context() -> None:
    stub_service = StubAuthService(None)
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.get("/api/v1/auth/session")
    finally:
        app.dependency_overrides.clear()

    assert stub_service.received_tokens == [None]
    assert_standard_error_response(
        response,
        status_code=401,
        code="authentication_required",
        message="Authentication is required.",
        details={},
    )


def test_auth_session_endpoint_reflects_pending_verification_access_limits() -> None:
    stub_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "verify-me")
        response = client.get("/api/v1/auth/session")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["security"] == {
        "email_verification_required": True,
        "can_access_support": True,
        "can_access_billing": False,
        "can_access_normal_authenticated_routes": False,
        "can_access_product_launch": False,
        "two_factor_enabled": False,
        "two_factor_method": None,
        "recovery_methods_available_count": 0,
        "recovery_codes_generated_at": None,
    }


def test_signup_endpoint_sets_session_cookie_and_returns_auth_session_payload() -> None:
    stub_service = StubAuthService(_build_context(status="pending_verification", email_verified_at=None))
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "username": "new-user",
                "email": "new-user@example.com",
                "password": "Password123",
            },
            headers={"user-agent": "signup-client"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert "zeptalytic_session=signup-token" in response.headers["set-cookie"]
    assert stub_service.signup_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="signup-client",
    )
    assert response.json()["account"]["status"] == "pending_verification"


def test_signup_endpoint_returns_conflict_error_for_duplicate_account() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "username": "duplicate",
                "email": "duplicate@example.com",
                "password": "Password123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=409,
        code="account_already_exists",
        message="An account with that username or email already exists.",
        details={"conflicts": ["email"]},
    )


def test_login_endpoint_sets_session_cookie_for_valid_credentials() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "auth-user@example.com",
                "password": "Password123",
            },
            headers={"user-agent": "login-client"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "zeptalytic_session=login-token" in response.headers["set-cookie"]
    assert stub_service.login_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="login-client",
    )


def test_verify_email_endpoint_returns_success_for_valid_token() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": "valid-token"},
            headers={"user-agent": "verify-client"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Email verified successfully."}
    assert stub_service.verify_calls[0] == {
        "token": "valid-token",
        "client_info": AuthClientInfo(ip_address="testclient", user_agent="verify-client"),
    }


def test_verify_email_endpoint_returns_invalid_token_error() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": "expired-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=400,
        code="email_verification_token_invalid",
        message="The email verification link is invalid or expired.",
        details={"reason": "expired"},
    )


def test_resend_verification_endpoint_uses_authenticated_pending_session() -> None:
    stub_service = StubAuthService(_build_context(status="pending_verification", email_verified_at=None))
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "resend-token")
        response = client.post(
            "/api/v1/auth/resend-verification",
            headers={"user-agent": "resend-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Verification email sent."}
    assert stub_service.received_tokens == ["resend-token"]
    assert stub_service.resend_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="resend-client",
    )


def test_forgot_password_endpoint_returns_generic_success_for_known_account() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "known@example.com"},
            headers={"user-agent": "forgot-client"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "If the account exists, password reset instructions have been sent.",
    }
    assert stub_service.forgot_password_calls[0] == {
        "email": "known@example.com",
        "client_info": AuthClientInfo(ip_address="testclient", user_agent="forgot-client"),
    }


def test_reset_password_endpoint_returns_success_for_valid_token() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "valid-reset-token", "new_password": "NewPassword123"},
            headers={"user-agent": "reset-client"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Password reset successfully."}
    assert stub_service.reset_password_calls[0] == {
        "token": "valid-reset-token",
        "new_password": "NewPassword123",
        "client_info": AuthClientInfo(ip_address="testclient", user_agent="reset-client"),
    }


def test_reset_password_endpoint_returns_invalid_token_error() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "expired-reset-token", "new_password": "NewPassword123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=400,
        code="password_reset_token_invalid",
        message="The password reset link is invalid or expired.",
        details={"reason": "expired"},
    )


def test_change_password_endpoint_rotates_cookie_for_authenticated_user() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "change-token")
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "Password123",
                "new_password": "NewPassword123",
            },
            headers={"user-agent": "change-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Password changed successfully."}
    assert "zeptalytic_session=changed-password-token" in response.headers["set-cookie"]
    assert stub_service.received_tokens == ["change-token"]
    assert stub_service.change_password_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="change-client",
    )


def test_change_password_endpoint_returns_current_password_error() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "change-token")
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewPassword123",
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=401,
        code="current_password_invalid",
        message="The current password is incorrect.",
        details={},
    )


def test_verified_guard_blocks_pending_verification_context() -> None:
    gated_app = FastAPI()
    register_request_id_middleware(gated_app)
    register_exception_handlers(gated_app)

    @gated_app.get("/gated")
    def gated_route(
        context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    ) -> dict[str, str]:
        return {"account_id": str(context.account_id)}

    stub_service = StubAuthService(_build_context(status="pending_verification", email_verified_at=None))
    gated_app.dependency_overrides[get_auth_service] = lambda: stub_service
    gated_client = TestClient(gated_app)

    try:
        gated_client.cookies.set("zeptalytic_session", "pending-token")
        response = gated_client.get("/gated")
    finally:
        gated_client.cookies.clear()
        gated_app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=403,
        code="email_verification_required",
        message="Email verification is required.",
        details={},
    )


def test_login_endpoint_returns_invalid_credentials_error() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "auth-user@example.com",
                "password": "WrongPassword123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=401,
        code="invalid_credentials",
        message="Invalid email or password.",
        details={},
    )


def test_login_endpoint_returns_account_access_restricted_for_closed_accounts() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "closed@example.com",
                "password": "Password123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=403,
        code="account_access_restricted",
        message="Account access is restricted.",
        details={"status": "closed"},
    )


def test_logout_endpoint_revokes_current_session_and_clears_cookie() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "logout-token")
        response = client.post(
            "/api/v1/auth/logout",
            json={"revoke_all_sessions": True},
            headers={"user-agent": "logout-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Logged out successfully."}
    assert "zeptalytic_session=\"\";" in response.headers["set-cookie"]
    assert stub_service.received_tokens == ["logout-token"]
    assert stub_service.logout_calls[0]["revoke_all_sessions"] is True
    assert stub_service.logout_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="logout-client",
    )


def test_two_factor_enrollment_endpoint_returns_provisioning_contract() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "mfa-token")
        response = client.post("/api/v1/auth/2fa/enroll")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["secret"] == "TESTSECRET"
    assert response.json()["otpauth_uri"].startswith("otpauth://totp/")


def test_two_factor_verify_endpoint_returns_recovery_codes() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "mfa-token")
        response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": "123456"},
            headers={"user-agent": "mfa-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Two-factor authentication enabled.",
        "recovery_codes": ["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"],
    }
    assert stub_service.verify_two_factor_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="mfa-client",
    )


def test_two_factor_challenge_endpoint_returns_error_for_used_recovery_code() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "mfa-token")
        response = client.post(
            "/api/v1/auth/2fa/challenge",
            json={"recovery_code": "USED-CODE"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=400,
        code="two_factor_code_invalid",
        message="The two-factor code is invalid.",
        details={"reason": "used"},
    )


def test_session_list_endpoint_returns_safe_device_contract() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "session-token")
        response = client.get("/api/v1/auth/sessions")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["sessions"][0]["is_current"] is True
    assert response.json()["sessions"][0]["ip_address"] == "127.0.0.1"


def test_revoke_session_endpoint_clears_cookie_for_current_session() -> None:
    context = _build_context()
    stub_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "session-token")
        response = client.post(f"/api/v1/auth/sessions/{context.session_id}/revoke")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Session revoked successfully."}
    assert "zeptalytic_session=\"\";" in response.headers["set-cookie"]


def test_revoke_other_sessions_endpoint_uses_authenticated_context() -> None:
    stub_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "session-token")
        response = client.post(
            "/api/v1/auth/sessions/revoke-others",
            headers={"user-agent": "revoke-others-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "All other sessions revoked successfully.",
    }
    assert stub_service.revoke_other_sessions_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="revoke-others-client",
    )


def test_account_closure_endpoint_clears_cookie_after_success() -> None:
    stub_service = StubAuthService(_build_context(two_factor_enabled=True, two_factor_method="totp"))
    app.dependency_overrides[get_auth_service] = lambda: stub_service

    try:
        client.cookies.set("zeptalytic_session", "close-token")
        response = client.post(
            "/api/v1/auth/account-closure",
            json={
                "current_password": "Password123",
                "code": "123456",
            },
            headers={"user-agent": "close-client"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Account closed successfully."}
    assert "zeptalytic_session=\"\";" in response.headers["set-cookie"]
    assert stub_service.close_account_calls[0]["client_info"] == AuthClientInfo(
        ip_address="testclient",
        user_agent="close-client",
    )
