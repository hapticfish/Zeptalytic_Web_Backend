from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_discord_integration_service
from app.integrations import DiscordOAuthStateValidationError
from app.main import app
from app.schemas.integrations import DiscordIntegrationReadResponse, DiscordIntegrationSummary
from app.services import (
    AuthenticatedSessionContext,
    DiscordIntegrationLinkNotFoundError,
    DiscordIntegrationNotFoundError,
)
from app.services.auth_service import EmailVerificationRequiredError


class StubDiscordIntegrationService:
    def __init__(self, response: DiscordIntegrationReadResponse | None = None) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    def get_integration(self, account_id):  # noqa: ANN001
        self.calls.append({"method": "get_integration", "account_id": account_id})
        if self._response is None:
            raise DiscordIntegrationNotFoundError(f"missing {account_id}")
        return self._response

    def build_connect_url(self, account_id):  # noqa: ANN001
        self.calls.append({"method": "build_connect_url", "account_id": account_id})
        return "https://discord.com/oauth2/authorize?state=signed-state"

    def complete_oauth_callback(self, account_id, *, code: str, state: str | None):  # noqa: ANN001
        self.calls.append(
            {
                "method": "complete_oauth_callback",
                "account_id": account_id,
                "code": code,
                "state": state,
            }
        )
        if code == "invalid-state":
            raise DiscordOAuthStateValidationError("expired_state")
        if self._response is None:
            raise DiscordIntegrationNotFoundError(f"missing {account_id}")
        return self._response

    def disconnect_discord_account(self, account_id):  # noqa: ANN001
        self.calls.append({"method": "disconnect_discord_account", "account_id": account_id})
        if self._response is None:
            raise DiscordIntegrationLinkNotFoundError(f"missing link {account_id}")
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
        username="discord-user",
        email="discord-user@example.com",
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


def _build_response(account_id) -> DiscordIntegrationReadResponse:  # noqa: ANN001
    return DiscordIntegrationReadResponse(
        discord=DiscordIntegrationSummary(
            account_id=account_id,
            username="linked-user#4242",
            integration_status="connected",
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )


client = TestClient(app)


def test_discord_integration_routes_require_verified_session_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = (
        lambda: StubDiscordIntegrationService()
    )

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.get("/api/v1/integrations/discord")
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


def test_discord_integration_status_endpoint_returns_safe_response() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(_build_response(context.account_id))
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.get("/api/v1/integrations/discord")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["discord-token"]
    assert integration_service.calls == [
        {"method": "get_integration", "account_id": context.account_id}
    ]
    assert response.json() == {
        "discord": {
            "account_id": str(context.account_id),
            "username": "linked-user#4242",
            "integration_status": "connected",
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T12:30:00Z",
        }
    }
    assert "discord_user_id" not in response.json()["discord"]


def test_discord_connect_endpoint_returns_authorization_url() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(_build_response(context.account_id))
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.post("/api/v1/integrations/discord/connect")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "authorization_url": "https://discord.com/oauth2/authorize?state=signed-state"
    }
    assert integration_service.calls == [
        {"method": "build_connect_url", "account_id": context.account_id}
    ]


def test_discord_callback_endpoint_completes_connection_with_query_params() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(_build_response(context.account_id))
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.get(
            "/api/v1/integrations/discord/callback",
            params={"code": "discord-auth-code", "state": "signed-state"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["discord"]["integration_status"] == "connected"
    assert integration_service.calls == [
        {
            "method": "complete_oauth_callback",
            "account_id": context.account_id,
            "code": "discord-auth-code",
            "state": "signed-state",
        }
    ]


def test_discord_callback_endpoint_uses_standard_error_shape_for_invalid_state() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(_build_response(context.account_id))
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.get(
            "/api/v1/integrations/discord/callback",
            params={"code": "invalid-state", "state": "expired-state"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "discord_oauth_state_invalid",
            "message": "Discord OAuth callback state is invalid.",
            "details": {"reason": "expired_state"},
        }
    }


def test_discord_disconnect_endpoint_returns_disconnected_state() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(
        DiscordIntegrationReadResponse(
            discord=DiscordIntegrationSummary(
                account_id=context.account_id,
                username=None,
                integration_status="disconnected",
                created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
            )
        )
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.post("/api/v1/integrations/discord/disconnect")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "discord": {
            "account_id": str(context.account_id),
            "username": None,
            "integration_status": "disconnected",
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T13:00:00Z",
        }
    }
    assert integration_service.calls == [
        {"method": "disconnect_discord_account", "account_id": context.account_id}
    ]


def test_discord_disconnect_endpoint_uses_standard_error_shape_for_missing_link() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = (
        lambda: StubDiscordIntegrationService()
    )

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        response = client.post("/api/v1/integrations/discord/disconnect")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "discord_integration_link_not_found",
            "message": "No active Discord connection was found.",
            "details": {},
        }
    }
