from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_billing_summary_service
from app.main import app
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingAddressBookSummary,
    BillingCheckoutInitiationRequest,
    BillingPaymentMethodsResponse,
    BillingPromoCodeRequest,
    BillingSnapshotResponse,
    BillingSubscriptionChangeRequest,
    BillingSubscriptionLifecycleRequest,
    BillingSubscriptionsResponse,
    BillingTransactionsPage,
    BillingTransactionsResponse,
)
from app.schemas.common import CursorPageInfo
from app.services.billing_summary_service import BillingActionUnavailableError
from app.services.auth_service import AuthenticatedSessionContext
from tests.unit.assertions import assert_standard_error_response


class StubBillingSummaryService:
    def __init__(
        self,
        *,
        snapshot: BillingSnapshotResponse,
        subscriptions: BillingSubscriptionsResponse,
        payment_methods: BillingPaymentMethodsResponse,
        transactions: BillingTransactionsResponse,
    ) -> None:
        self._snapshot = snapshot
        self._subscriptions = subscriptions
        self._payment_methods = payment_methods
        self._transactions = transactions
        self.snapshot_calls: list[object] = []
        self.subscription_calls: list[object] = []
        self.payment_method_calls: list[object] = []
        self.transaction_calls: list[dict[str, object]] = []
        self.checkout_calls: list[dict[str, object]] = []
        self.subscription_change_calls: list[dict[str, object]] = []
        self.subscription_cancel_calls: list[dict[str, object]] = []
        self.subscription_restart_calls: list[dict[str, object]] = []
        self.promo_validation_calls: list[dict[str, object]] = []
        self.promo_apply_calls: list[dict[str, object]] = []
        self.checkout_error: Exception | None = None

    def get_snapshot(self, account_id):  # noqa: ANN001
        self.snapshot_calls.append(account_id)
        return self._snapshot

    def list_subscriptions(self, account_id):  # noqa: ANN001
        self.subscription_calls.append(account_id)
        return self._subscriptions

    def list_payment_methods(self, account_id):  # noqa: ANN001
        self.payment_method_calls.append(account_id)
        return self._payment_methods

    def list_transactions(self, account_id, *, limit: int = 25, cursor: str | None = None):  # noqa: ANN001
        self.transaction_calls.append(
            {"account_id": account_id, "limit": limit, "cursor": cursor}
        )
        return self._transactions

    def initiate_checkout(self, account_id, payload: BillingCheckoutInitiationRequest):  # noqa: ANN001
        self.checkout_calls.append({"account_id": account_id, "payload": payload})
        if self.checkout_error is not None:
            raise self.checkout_error
        return BillingActionInitiationResponse(
            message="Checkout initiated.",
            action="checkout",
            pay_result={"pay_redirect_url": "https://pay.example/checkout/session_001"},
        )

    def initiate_subscription_change(
        self,
        account_id,
        payload: BillingSubscriptionChangeRequest,
    ):  # noqa: ANN001
        self.subscription_change_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Subscription change initiated.",
            action="subscription_change",
            pay_result={"pay_session_id": "change_001"},
        )

    def initiate_subscription_cancel(
        self,
        account_id,
        payload: BillingSubscriptionLifecycleRequest,
    ):  # noqa: ANN001
        self.subscription_cancel_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Subscription cancellation initiated.",
            action="subscription_cancel",
        )

    def initiate_subscription_restart(
        self,
        account_id,
        payload: BillingSubscriptionLifecycleRequest,
    ):  # noqa: ANN001
        self.subscription_restart_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Subscription restart initiated.",
            action="subscription_restart",
        )

    def validate_promo_code(self, account_id, payload: BillingPromoCodeRequest):  # noqa: ANN001
        self.promo_validation_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Promo code validated.",
            action="promo_code_validation",
        )

    def apply_promo_code(self, account_id, payload: BillingPromoCodeRequest):  # noqa: ANN001
        self.promo_apply_calls.append({"account_id": account_id, "payload": payload})
        return BillingActionInitiationResponse(
            message="Promo code applied.",
            action="promo_code_apply",
        )


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


def _build_context(*, status: str = "active") -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="billing-user",
        email="billing-user@example.com",
        status=status,
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


def _build_billing_service() -> StubBillingSummaryService:
    return StubBillingSummaryService(
        snapshot=BillingSnapshotResponse(
            pay_integration_status="available",
            pay_projection_billing=None,
            parent_billing_addresses=BillingAddressBookSummary(total_saved_count=0, addresses=[]),
        ),
        subscriptions=BillingSubscriptionsResponse(
            pay_integration_status="available",
            pay_subscriptions=[],
        ),
        payment_methods=BillingPaymentMethodsResponse(
            pay_integration_status="available",
            pay_payment_methods=[],
        ),
        transactions=BillingTransactionsResponse(
            pay_integration_status="available",
            pay_transactions=BillingTransactionsPage(
                items=[],
                page=CursorPageInfo(limit=25, cursor=None, next_cursor=None),
            ),
        ),
    )


client = TestClient(app)


def test_billing_endpoints_allow_suspended_authenticated_sessions() -> None:
    context = _build_context(status="suspended")
    auth_service = StubAuthService(context)
    billing_service = _build_billing_service()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_billing_summary_service] = lambda: billing_service

    try:
        client.cookies.set("zeptalytic_session", "billing-token")
        snapshot_response = client.get("/api/v1/billing/snapshot")
        subscriptions_response = client.get("/api/v1/billing/subscriptions")
        payment_methods_response = client.get("/api/v1/billing/payment-methods")
        transactions_response = client.get(
            "/api/v1/billing/transactions",
            params={"limit": 10, "cursor": "txn_001"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert snapshot_response.status_code == 200
    assert subscriptions_response.status_code == 200
    assert payment_methods_response.status_code == 200
    assert transactions_response.status_code == 200
    assert auth_service.received_tokens == [
        "billing-token",
        "billing-token",
        "billing-token",
        "billing-token",
    ]
    assert billing_service.snapshot_calls == [context.account_id]
    assert billing_service.subscription_calls == [context.account_id]
    assert billing_service.payment_method_calls == [context.account_id]
    assert billing_service.transaction_calls == [
        {"account_id": context.account_id, "limit": 10, "cursor": "txn_001"}
    ]


def test_billing_transactions_endpoint_validates_limit_with_standard_error_shape() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_billing_summary_service] = lambda: _build_billing_service()

    try:
        client.cookies.set("zeptalytic_session", "billing-token")
        response = client.get("/api/v1/billing/transactions", params={"limit": 0})
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_billing_checkout_endpoint_delegates_action_for_suspended_authenticated_session() -> None:
    context = _build_context(status="suspended")
    auth_service = StubAuthService(context)
    billing_service = _build_billing_service()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_billing_summary_service] = lambda: billing_service

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
    assert response.json() == {
        "success": True,
        "message": "Checkout initiated.",
        "action": "checkout",
        "pay_result": {
            "pay_redirect_url": "https://pay.example/checkout/session_001",
            "pay_session_id": None,
            "pay_client_secret": None,
        },
    }
    assert billing_service.checkout_calls[0]["account_id"] == context.account_id
    assert billing_service.checkout_calls[0]["payload"] == BillingCheckoutInitiationRequest(
        product_code="zardbot",
        plan_code="starter-monthly",
        billing_interval="monthly",
        success_url="https://app.example/success",
        cancel_url="https://app.example/cancel",
    )


def test_billing_checkout_endpoint_returns_standard_error_when_pay_is_unavailable() -> None:
    auth_service = StubAuthService(_build_context(status="suspended"))
    billing_service = _build_billing_service()
    billing_service.checkout_error = BillingActionUnavailableError("checkout")
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_billing_summary_service] = lambda: billing_service

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

    assert_standard_error_response(
        response,
        status_code=503,
        code="billing_action_unavailable",
        message="Billing action is temporarily unavailable.",
        details={"action": "checkout"},
    )
