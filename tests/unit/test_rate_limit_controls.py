from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import (
    get_audit_hook,
    get_auth_service,
    get_billing_summary_service,
    get_discord_integration_service,
    get_rate_limiter,
    get_support_service,
)
from app.main import app
from app.schemas.billing import BillingActionInitiationResponse
from app.schemas.integrations import DiscordIntegrationReadResponse, DiscordIntegrationSummary
from app.schemas.support import SupportTicketCreateResponse, SupportTicketSummary
from app.services import AuthClientInfo, AuthMutationResult, AuthenticatedSessionContext
from app.utils.audit import InMemoryAuditHook, sanitize_audit_metadata
from app.utils.rate_limits import InMemoryRateLimiter
from tests.unit.assertions import assert_standard_error_response


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context
        self.login_calls: list[dict[str, object]] = []
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
        assert self._context is not None
        return AuthMutationResult(session_token="login-token", context=self._context)


class StubBillingSummaryService:
    def __init__(self) -> None:
        self.checkout_calls: list[dict[str, object]] = []

    def initiate_checkout(self, account_id, payload):  # noqa: ANN001
        self.checkout_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Checkout initiated.",
            action="checkout",
            pay_result={"pay_redirect_url": "https://pay.example/checkout/session_001"},
        )


class StubDiscordIntegrationService:
    def __init__(self, account_id) -> None:  # noqa: ANN001
        self.account_id = account_id
        self.callback_calls: list[dict[str, object]] = []

    def complete_oauth_callback(self, account_id, *, code: str, state: str | None):  # noqa: ANN001
        self.callback_calls.append({"account_id": account_id, "code": code, "state": state})
        return DiscordIntegrationReadResponse(
            discord=DiscordIntegrationSummary(
                account_id=self.account_id,
                username="linked-user#4242",
                integration_status="connected",
                created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
            )
        )


class StubSupportService:
    def __init__(self) -> None:
        self.create_calls: list[dict[str, object]] = []

    def create_ticket(self, context: AuthenticatedSessionContext, payload) -> SupportTicketCreateResponse:  # noqa: ANN001
        self.create_calls.append({"context": context, "payload": payload})
        return SupportTicketCreateResponse(
            message="Support ticket created.",
            ticket=SupportTicketSummary(
                ticket_id=uuid4(),
                ticket_code="SUP-1002",
                request_type=payload.request_type,
                related_product_code=payload.related_product_code,
                priority=payload.priority,
                subject=payload.subject,
                status="open",
                estimated_response_sla_label="Estimated response: within 1 business day.",
                created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 18, 12, 5, tzinfo=timezone.utc),
                attachment_count=len(payload.attachments),
            ),
        )


def _build_context() -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="security-user",
        email="security-user@example.com",
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


client = TestClient(app)


def test_login_endpoint_rate_limits_after_repeated_attempts() -> None:
    limiter = InMemoryRateLimiter()
    audit_hook = InMemoryAuditHook()
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_audit_hook] = lambda: audit_hook

    try:
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "security-user@example.com", "password": "Password123"},
            )
            assert response.status_code == 200

        blocked_response = client.post(
            "/api/v1/auth/login",
            json={"email": "security-user@example.com", "password": "Password123"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        blocked_response,
        status_code=429,
        code="rate_limit_exceeded",
        message="Rate limit exceeded. Please retry later.",
        details={
            "action": "auth_login",
            "retry_after_seconds": blocked_response.json()["error"]["details"][
                "retry_after_seconds"
            ],
        },
    )
    assert int(blocked_response.headers["Retry-After"]) >= 1
    assert len(audit_hook.events) == 10


def test_billing_checkout_emits_safe_audit_events() -> None:
    context = _build_context()
    limiter = InMemoryRateLimiter()
    audit_hook = InMemoryAuditHook()
    auth_service = StubAuthService(context)
    billing_service = StubBillingSummaryService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_billing_summary_service] = lambda: billing_service
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_audit_hook] = lambda: audit_hook

    try:
        client.cookies.set("zeptalytic_session", "billing-token")
        response = client.post(
            "/api/v1/billing/checkout",
            json={
                "product_code": "zardbot",
                "plan_code": "starter-monthly",
                "billing_interval": "monthly",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [event.action for event in audit_hook.events] == [
        "billing.checkout",
        "billing.checkout",
    ]
    assert audit_hook.events[0].metadata == {
        "product_code": "zardbot",
        "plan_code": "starter-monthly",
        "billing_interval": "monthly",
    }
    assert audit_hook.events[0].account_id == str(context.account_id)


def test_discord_callback_endpoint_rate_limits_repeated_requests() -> None:
    context = _build_context()
    limiter = InMemoryRateLimiter()
    audit_hook = InMemoryAuditHook()
    auth_service = StubAuthService(context)
    integration_service = StubDiscordIntegrationService(context.account_id)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_discord_integration_service] = lambda: integration_service
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_audit_hook] = lambda: audit_hook

    try:
        client.cookies.set("zeptalytic_session", "discord-token")
        for _ in range(10):
            response = client.get(
                "/api/v1/integrations/discord/callback",
                params={"code": "discord-auth-code", "state": "signed-state"},
            )
            assert response.status_code == 200

        blocked_response = client.get(
            "/api/v1/integrations/discord/callback",
            params={"code": "discord-auth-code", "state": "signed-state"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        blocked_response,
        status_code=429,
        code="rate_limit_exceeded",
        message="Rate limit exceeded. Please retry later.",
        details={
            "action": "discord_callback",
            "retry_after_seconds": blocked_response.json()["error"]["details"][
                "retry_after_seconds"
            ],
        },
    )


def test_support_ticket_audit_events_exclude_sensitive_body_fields() -> None:
    context = _build_context()
    limiter = InMemoryRateLimiter()
    audit_hook = InMemoryAuditHook()
    auth_service = StubAuthService(context)
    support_service = StubSupportService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_support_service] = lambda: support_service
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_audit_hook] = lambda: audit_hook

    try:
        client.cookies.set("zeptalytic_session", "support-token")
        response = client.post(
            "/api/v1/support/tickets",
            json={
                "request_type": "technical_support",
                "related_product_code": "zardbot",
                "priority": "medium",
                "subject": "Need help",
                "description": "The launcher is blocked after login.",
                "attachments": [],
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert audit_hook.events[0].metadata == {
        "request_type": "technical_support",
        "related_product_code": "zardbot",
        "priority": "medium",
        "attachment_count": 0,
    }


def test_sanitize_audit_metadata_drops_sensitive_fields() -> None:
    sanitized = sanitize_audit_metadata(
        {
            "product_code": "zardbot",
            "token": "raw-token",
            "subject": "Need help",
            "description": "Sensitive support details",
            "password": "Password123",
            "attachment_count": 2,
        }
    )

    assert sanitized == {
        "product_code": "zardbot",
        "attachment_count": 2,
    }
