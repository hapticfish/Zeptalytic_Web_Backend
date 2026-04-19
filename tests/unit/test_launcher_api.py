from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_launcher_service
from app.main import app
from app.schemas.launcher import LauncherProductsResponse
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)


class StubLauncherService:
    def __init__(self, response: LauncherProductsResponse) -> None:
        self._response = response
        self.requested_contexts: list[AuthenticatedSessionContext] = []

    def get_products(self, context: AuthenticatedSessionContext) -> LauncherProductsResponse:
        self.requested_contexts.append(context)
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
        username="launcher-user",
        email="launcher-user@example.com",
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


def test_launcher_products_endpoint_returns_service_payload() -> None:
    context = _build_context()
    launcher_service = StubLauncherService(
        LauncherProductsResponse(pay_integration_status="available", products=[])
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_launcher_service] = lambda: launcher_service

    try:
        client.cookies.set("zeptalytic_session", "launcher-token")
        response = client.get("/api/v1/launcher/products")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["launcher-token"]
    assert launcher_service.requested_contexts == [context]
    assert response.json() == {
        "pay_integration_status": "available",
        "products": [],
    }


def test_launcher_products_endpoint_requires_verified_session() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_launcher_service] = lambda: StubLauncherService(
        LauncherProductsResponse(pay_integration_status="available", products=[])
    )

    try:
        client.cookies.set("zeptalytic_session", "launcher-token")
        response = client.get("/api/v1/launcher/products")
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
