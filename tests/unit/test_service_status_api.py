from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_service_status_service
from app.main import app
from app.schemas.service_status import ServiceStatusListItem, ServiceStatusListResponse
from app.services.auth_service import AuthenticatedSessionContext


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


class StubServiceStatusService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_current_statuses(
        self,
        *,
        product_codes: list[str] | None,
    ) -> ServiceStatusListResponse:
        self.calls.append({"product_codes": product_codes})
        return ServiceStatusListResponse(
            items=[
                ServiceStatusListItem(
                    status_id=uuid4(),
                    product_code="zardbot",
                    status="degraded",
                    message="Delayed launches under investigation.",
                    updated_at=datetime(2026, 4, 18, 20, 0, tzinfo=timezone.utc),
                )
            ]
        )


def _build_context() -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="status-user",
        email="status-user@example.com",
        status="pending_verification",
        role="user",
        email_verified_at=None,
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


def test_service_status_endpoint_returns_service_payload_with_filters() -> None:
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService(_build_context())
    service_status_service = StubServiceStatusService()
    app.dependency_overrides[get_service_status_service] = lambda: service_status_service

    try:
        client.cookies.set("zeptalytic_session", "status-token")
        response = client.get(
            "/api/v1/service-status",
            params=[("product_code", "zardbot"), ("product_code", "zepta")],
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service_status_service.calls == [{"product_codes": ["zardbot", "zepta"]}]
    assert response.json()["items"][0]["status"] == "degraded"
