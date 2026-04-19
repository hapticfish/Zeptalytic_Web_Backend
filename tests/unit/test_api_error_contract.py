from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.api.exception_handlers import register_exception_handlers
from app.integrations import DiscordOAuthStateValidationError
from app.main import app
from app.services.auth_service import AuthenticatedSessionContext

client = TestClient(app)


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context

    def get_authenticated_session_context(
        self,
        session_token: str | None,
    ) -> AuthenticatedSessionContext | None:
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
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context


def _build_context() -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="rewards-user",
        email="rewards-user@example.com",
        status="active",
        role="user",
        email_verified_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
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


def test_invalid_uuid_returns_standard_validation_error_shape() -> None:
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService(_build_context())

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.post("/api/v1/rewards/me/notifications/not-a-uuid/seen")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation failed."
    assert payload["error"]["details"] == {
        "errors": [
            {
                "loc": ["path", "notification_id"],
                "msg": payload["error"]["details"]["errors"][0]["msg"],
                "type": "uuid_parsing",
            }
        ]
    }


def test_discord_oauth_state_errors_use_standard_error_shape() -> None:
    local_app = FastAPI()
    register_exception_handlers(local_app)

    @local_app.get("/test/discord-oauth-state")
    def discord_oauth_state_failure() -> None:
        raise DiscordOAuthStateValidationError("expired_state")

    response = TestClient(local_app).get("/test/discord-oauth-state")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "discord_oauth_state_invalid",
            "message": "Discord OAuth callback state is invalid.",
            "details": {"reason": "expired_state"},
        }
    }
