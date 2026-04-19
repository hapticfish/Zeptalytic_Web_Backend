from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_dashboard_service
from app.main import app
from app.schemas.billing import BillingAddressBookSummary, BillingSnapshotResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.launcher import LauncherProductsResponse
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)


class StubDashboardService:
    def __init__(self, response: DashboardSummaryResponse) -> None:
        self._response = response
        self.requested_contexts: list[AuthenticatedSessionContext] = []

    def get_summary(self, context: AuthenticatedSessionContext) -> DashboardSummaryResponse:
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
        username="dashboard-user",
        email="dashboard-user@example.com",
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


def test_dashboard_summary_endpoint_returns_service_payload() -> None:
    context = _build_context()
    dashboard_service = StubDashboardService(
        DashboardSummaryResponse(
            launcher=LauncherProductsResponse(pay_integration_status="available", products=[]),
            billing=BillingSnapshotResponse(
                pay_integration_status="available",
                pay_projection_billing=None,
                parent_billing_addresses=BillingAddressBookSummary(
                    total_saved_count=0,
                    addresses=[],
                ),
            ),
            parent_notifications=[],
            parent_system_statuses=[],
        )
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_dashboard_service] = lambda: dashboard_service

    try:
        client.cookies.set("zeptalytic_session", "dashboard-token")
        response = client.get("/api/v1/dashboard/summary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["dashboard-token"]
    assert dashboard_service.requested_contexts == [context]
    assert response.json()["launcher"]["pay_integration_status"] == "available"


def test_dashboard_summary_endpoint_requires_verified_session() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_dashboard_service] = lambda: StubDashboardService(
        DashboardSummaryResponse(
            launcher=LauncherProductsResponse(pay_integration_status="available", products=[]),
            billing=BillingSnapshotResponse(
                pay_integration_status="available",
                pay_projection_billing=None,
                parent_billing_addresses=BillingAddressBookSummary(
                    total_saved_count=0,
                    addresses=[],
                ),
            ),
            parent_notifications=[],
            parent_system_statuses=[],
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "dashboard-token")
        response = client.get("/api/v1/dashboard/summary")
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
