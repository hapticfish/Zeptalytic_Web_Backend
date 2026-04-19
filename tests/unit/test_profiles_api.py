from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_profile_settings_service
from app.main import app
from app.schemas.profiles import ProfileSettingsReadResponse, ProfileSettingsSummary
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)


class StubProfileSettingsService:
    def __init__(self, response: ProfileSettingsReadResponse | None = None) -> None:
        self._response = response

    def describe_contract(self):  # noqa: ANN001
        return {
            "success": True,
            "message": "Profiles router registered.",
            "scope": "profiles",
            "guard": "normal_authenticated_verified",
        }

    def get_profile_settings(self, account_id):  # noqa: ANN001
        if self._response is None:
            from app.services.profile_settings_service import ProfileSettingsNotFoundError

            raise ProfileSettingsNotFoundError(f"missing {account_id}")
        return self._response


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context
        self.received_tokens: list[str | None] = []

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


def _build_context(
    *,
    status: str = "active",
    email_verified_at: datetime | None = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
) -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="profile-user",
        email="profile-user@example.com",
        status=status,
        role="user",
        email_verified_at=email_verified_at,
        session_created_at=now - timedelta(hours=1),
        session_expires_at=now + timedelta(hours=1),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest-client",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


client = TestClient(app)


def test_profiles_contract_endpoint_uses_verified_session_guard() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_profile_settings_service] = lambda: StubProfileSettingsService()

    try:
        client.cookies.set("zeptalytic_session", "profiles-token")
        response = client.get("/api/v1/profiles/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["profiles-token"]
    assert response.json() == {
        "success": True,
        "message": "Profiles router registered.",
        "scope": "profiles",
        "guard": "normal_authenticated_verified",
    }


def test_profiles_contract_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_profile_settings_service] = lambda: StubProfileSettingsService()

    try:
        client.cookies.set("zeptalytic_session", "profiles-token")
        response = client.get("/api/v1/profiles/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "email_verification_required",
            "message": "Email verification is required.",
            "details": {},
        }
    }


def test_profiles_me_endpoint_returns_profile_settings_summary() -> None:
    context = _build_context()
    response_payload = ProfileSettingsReadResponse(
        profile=ProfileSettingsSummary(
            account_id=context.account_id,
            username="profile-user",
            email="profile-user@example.com",
            display_name="Profile User",
            phone="+1-312-555-0101",
            timezone="America/Chicago",
            profile_image_url="https://cdn.example.com/profiles/profile-user.png",
            preferred_language="en",
            discord={
                "username": "profile-user#1234",
                "integration_status": "connected",
            },
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_profile_settings_service] = (
        lambda: StubProfileSettingsService(response_payload)
    )

    try:
        client.cookies.set("zeptalytic_session", "profiles-token")
        response = client.get("/api/v1/profiles/me")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["profiles-token"]
    assert response.json() == {
        "profile": {
            "account_id": str(context.account_id),
            "username": "profile-user",
            "email": "profile-user@example.com",
            "display_name": "Profile User",
            "phone": "+1-312-555-0101",
            "timezone": "America/Chicago",
            "profile_image_url": "https://cdn.example.com/profiles/profile-user.png",
            "preferred_language": "en",
            "discord": {
                "username": "profile-user#1234",
                "integration_status": "connected",
            },
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T12:30:00Z",
        }
    }


def test_profiles_me_endpoint_returns_not_found_when_profile_settings_missing() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_profile_settings_service] = lambda: StubProfileSettingsService(None)

    try:
        client.cookies.set("zeptalytic_session", "profiles-token")
        response = client.get("/api/v1/profiles/me")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "profile_settings_not_found",
            "message": "Profile settings not found.",
            "details": {},
        }
    }
