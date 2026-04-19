from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_support_service
from app.main import app
from app.schemas.common import CursorPageInfo
from app.schemas.support import (
    SupportRouteContractResponse,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    SupportTicketSummary,
)
from app.services.auth_service import (
    AuthenticatedSessionContext,
    AuthenticationRequiredError,
)
from app.services.support_service import (
    SupportAccessRestrictedError,
    SupportTicketNotFoundError,
)
from tests.unit.assertions import assert_standard_error_response


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
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context


class StubSupportService:
    def __init__(self) -> None:
        self.list_calls: list[dict[str, object]] = []
        self.detail_calls: list[dict[str, object]] = []
        self.create_calls: list[dict[str, object]] = []
        self.ticket_id = uuid4()
        self.ticket_summary = SupportTicketSummary(
            ticket_id=self.ticket_id,
            ticket_code="SUP-1001",
            request_type="technical_support",
            related_product_code="zardbot",
            priority="medium",
            subject="Need help",
            status="open",
            estimated_response_sla_label="Estimated response: within 1 business day.",
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 5, tzinfo=timezone.utc),
            attachment_count=0,
        )

    def describe_contract(self) -> SupportRouteContractResponse:
        return SupportRouteContractResponse(
            message="Support routes registered.",
            action="create_ticket",
        )

    def list_tickets(
        self,
        context: AuthenticatedSessionContext,
        *,
        limit: int,
        cursor: str | None,
    ) -> SupportTicketListResponse:
        self.list_calls.append({"context": context, "limit": limit, "cursor": cursor})
        return SupportTicketListResponse(
            items=[self.ticket_summary],
            page=CursorPageInfo(limit=limit, cursor=cursor, next_cursor="next-ticket"),
        )

    def get_ticket_detail(
        self,
        context: AuthenticatedSessionContext,
        ticket_id,
    ) -> SupportTicketDetailResponse:
        self.detail_calls.append({"context": context, "ticket_id": ticket_id})
        if str(ticket_id).endswith("ffff"):
            raise SupportTicketNotFoundError("missing")
        return SupportTicketDetailResponse(
            ticket=self.ticket_summary,
            description="Product launch failed after login.",
            attachments=[],
        )

    def create_ticket(
        self,
        context: AuthenticatedSessionContext,
        payload,
    ) -> SupportTicketCreateResponse:
        self.create_calls.append({"context": context, "payload": payload})
        if payload.subject == "blocked":
            raise SupportAccessRestrictedError("closed")
        return SupportTicketCreateResponse(
            message="Support ticket created.",
            ticket=self.ticket_summary,
        )


def _build_context(
    *,
    status: str = "pending_verification",
    email_verified_at: datetime | None = None,
) -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="support-user",
        email="support-user@example.com",
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


def test_support_contract_endpoint_allows_authenticated_pending_verification_users() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: StubSupportService()

    try:
        client.cookies.set("zeptalytic_session", "support-token")
        response = client.get("/api/v1/support/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["support-token"]
    assert response.json() == {
        "success": True,
        "message": "Support routes registered.",
        "action": "create_ticket",
    }


def test_support_ticket_endpoints_allow_authenticated_pending_verification_users() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    support_service = StubSupportService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: support_service

    try:
        client.cookies.set("zeptalytic_session", "support-token")
        list_response = client.get("/api/v1/support/tickets", params={"limit": 5, "cursor": "abc"})
        detail_response = client.get(f"/api/v1/support/tickets/{support_service.ticket_id}")
        create_response = client.post(
            "/api/v1/support/tickets",
            json={
                "request_type": "technical_support",
                "related_product_code": "zardbot",
                "priority": "medium",
                "subject": "Need help",
                "description": "The launcher is blocked.",
                "attachments": [],
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert create_response.status_code == 200
    assert auth_service.received_tokens == ["support-token", "support-token", "support-token"]
    assert support_service.list_calls[0]["context"] == context
    assert support_service.list_calls[0]["limit"] == 5
    assert support_service.list_calls[0]["cursor"] == "abc"
    assert support_service.detail_calls[0]["context"] == context
    assert support_service.create_calls[0]["context"] == context
    assert list_response.json()["page"]["next_cursor"] == "next-ticket"
    assert create_response.json()["ticket"]["ticket_code"] == "SUP-1001"


def test_support_ticket_detail_returns_standard_not_found_error() -> None:
    context = _build_context(status="active", email_verified_at=datetime.now(timezone.utc))
    auth_service = StubAuthService(context)
    support_service = StubSupportService()
    missing_ticket_id = "00000000-0000-0000-0000-00000000ffff"
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: support_service

    try:
        client.cookies.set("zeptalytic_session", "support-token")
        response = client.get(f"/api/v1/support/tickets/{missing_ticket_id}")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=404,
        code="support_ticket_not_found",
        message="Support ticket not found.",
        details={},
    )


def test_support_ticket_create_returns_standard_restricted_error() -> None:
    context = _build_context(status="active", email_verified_at=datetime.now(timezone.utc))
    auth_service = StubAuthService(context)
    support_service = StubSupportService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: support_service

    try:
        client.cookies.set("zeptalytic_session", "support-token")
        response = client.post(
            "/api/v1/support/tickets",
            json={
                "request_type": "technical_support",
                "related_product_code": "zardbot",
                "priority": "medium",
                "subject": "blocked",
                "description": "The account should be blocked.",
                "attachments": [],
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=403,
        code="support_access_restricted",
        message="Support access is restricted.",
        details={"status": "closed"},
    )


def test_support_ticket_endpoints_require_authentication() -> None:
    auth_service = StubAuthService(None)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: StubSupportService()

    try:
        response = client.get("/api/v1/support/tickets")
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=401,
        code="authentication_required",
        message="Authentication is required.",
        details={},
    )


def test_support_contract_endpoint_requires_authentication() -> None:
    auth_service = StubAuthService(None)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: StubSupportService()

    try:
        response = client.get("/api/v1/support/_contract")
    finally:
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=401,
        code="authentication_required",
        message="Authentication is required.",
        details={},
    )
