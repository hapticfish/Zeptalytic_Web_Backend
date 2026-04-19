from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_announcement_service, get_auth_service
from app.main import app
from app.schemas.announcements import AnnouncementListItem, AnnouncementListResponse
from app.schemas.common import CursorPageInfo
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


class StubAnnouncementService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_announcements(
        self,
        *,
        product_codes: list[str] | None,
        limit: int,
        cursor: str | None,
    ) -> AnnouncementListResponse:
        self.calls.append(
            {"product_codes": product_codes, "limit": limit, "cursor": cursor}
        )
        return AnnouncementListResponse(
            items=[
                AnnouncementListItem(
                    announcement_id=uuid4(),
                    scope="product",
                    product_code="zardbot",
                    title="Maintenance window",
                    body="Scheduled maintenance tonight.",
                    severity="warning",
                    published_at=datetime(2026, 4, 18, 18, 0, tzinfo=timezone.utc),
                    expires_at=None,
                )
            ],
            page=CursorPageInfo(limit=limit, cursor=cursor, next_cursor=None),
        )


def _build_context() -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="announcement-user",
        email="announcement-user@example.com",
        status="suspended",
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


def test_announcement_endpoint_returns_service_payload_with_filters() -> None:
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService(_build_context())
    announcement_service = StubAnnouncementService()
    app.dependency_overrides[get_announcement_service] = lambda: announcement_service

    try:
        client.cookies.set("zeptalytic_session", "announcement-token")
        response = client.get(
            "/api/v1/announcements",
            params=[("limit", "5"), ("product_code", "zardbot"), ("product_code", "zepta")],
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert announcement_service.calls == [
        {"product_codes": ["zardbot", "zepta"], "limit": 5, "cursor": None}
    ]
    assert response.json()["items"][0]["severity"] == "warning"
