from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import app.api.routers.v1.billing as billing_router
from app.api.deps import (
    get_audit_hook,
    get_billing_summary_service,
    get_rate_limiter,
    require_authenticated_session_context,
)
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingActionResult,
    BillingAddressBookSummary,
    BillingPaymentMethodSummary,
    BillingPaymentMethodsResponse,
    BillingSnapshotPayProjectionSummary,
    BillingSnapshotResponse,
    BillingSubscriptionSummary,
    BillingSubscriptionsResponse,
    BillingTransactionSummary,
    BillingTransactionsPage,
    BillingTransactionsResponse,
)
from app.schemas.common import CursorPageInfo
from app.services.auth_service import AuthenticatedSessionContext


class StubBillingSummaryService:
    def __init__(self) -> None:
        self.snapshot_calls: list[UUID] = []
        self.subscription_calls: list[UUID] = []
        self.payment_method_calls: list[UUID] = []
        self.transaction_calls: list[dict[str, object]] = []
        self.checkout_calls: list[dict[str, object]] = []
        self.subscription_change_calls: list[dict[str, object]] = []
        self.subscription_cancel_calls: list[dict[str, object]] = []
        self.subscription_restart_calls: list[dict[str, object]] = []
        self.promo_validate_calls: list[dict[str, object]] = []
        self.promo_apply_calls: list[dict[str, object]] = []

    def get_snapshot(self, account_id: UUID) -> BillingSnapshotResponse:
        self.snapshot_calls.append(account_id)
        return BillingSnapshotResponse(
            pay_integration_status="available",
            pay_projection_billing=BillingSnapshotPayProjectionSummary(
                subscribed_products=[
                    BillingSubscriptionSummary(
                        source="pay_projection",
                        product_code="ZEPTA",
                        product_name="Zepta",
                        plan_code="zepta_lvl_1",
                        subscription_status="active",
                        billing_interval="month",
                        current_charge_amount_cents=5500,
                        currency="USD",
                        next_payment_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
                        cancel_at_period_end=False,
                    )
                ],
                current_payment_method=BillingPaymentMethodSummary(
                    source="pay_projection",
                    provider="stripe",
                    method_type="card",
                    display_label="Visa ending in 4242",
                    brand="visa",
                    last4="4242",
                    exp_month=12,
                    exp_year=2030,
                    cardholder_name="Billing User",
                    billing_country="US",
                    is_default=True,
                    status="active",
                ),
            ),
            parent_billing_addresses=BillingAddressBookSummary(
                total_saved_count=0,
                addresses=[],
            ),
        )

    def list_subscriptions(self, account_id: UUID) -> BillingSubscriptionsResponse:
        self.subscription_calls.append(account_id)
        return BillingSubscriptionsResponse(
            pay_integration_status="available",
            pay_subscriptions=[
                BillingSubscriptionSummary(
                    source="pay_projection",
                    product_code="ZEPTA",
                    product_name="Zepta",
                    plan_code="zepta_lvl_1",
                    subscription_status="active",
                    billing_interval="month",
                    current_charge_amount_cents=5500,
                    currency="USD",
                    next_payment_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
                    cancel_at_period_end=False,
                )
            ],
        )

    def list_payment_methods(self, account_id: UUID) -> BillingPaymentMethodsResponse:
        self.payment_method_calls.append(account_id)
        return BillingPaymentMethodsResponse(
            pay_integration_status="available",
            pay_payment_methods=[
                BillingPaymentMethodSummary(
                    source="pay_projection",
                    provider="stripe",
                    method_type="card",
                    display_label="Visa ending in 4242",
                    brand="visa",
                    last4="4242",
                    exp_month=12,
                    exp_year=2030,
                    cardholder_name="Billing User",
                    billing_country="US",
                    is_default=True,
                    status="active",
                )
            ],
        )

    def list_transactions(
        self,
        account_id: UUID,
        *,
        limit: int = 25,
        cursor: str | None = None,
    ) -> BillingTransactionsResponse:
        self.transaction_calls.append(
            {
                "account_id": account_id,
                "limit": limit,
                "cursor": cursor,
            }
        )
        return BillingTransactionsResponse(
            pay_integration_status="available",
            pay_transactions=BillingTransactionsPage(
                items=[
                    BillingTransactionSummary(
                        source="pay_projection",
                        occurred_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
                        description="Zepta payment via card",
                        amount_cents=5500,
                        currency="USD",
                        status="succeeded",
                        product_code="ZEPTA",
                    )
                ],
                page=CursorPageInfo(limit=limit, cursor=cursor, next_cursor=None),
            ),
        )

    def initiate_checkout(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.checkout_calls.append(
            {
                "account_id": account_id,
                "payload": payload,
            }
        )
        return BillingActionInitiationResponse(
            message="Checkout initiated.",
            action="checkout",
            pay_result=BillingActionResult(
                pay_redirect_url="https://pay.example.test/session/checkout_123",
                pay_session_id="checkout_123",
                pay_client_secret=None,
            ),
        )

    def initiate_subscription_change(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.subscription_change_calls.append({"account_id": account_id, "payload": payload})
        raise AssertionError("Unsupported subscription-change route must not call service.")

    def initiate_subscription_cancel(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.subscription_cancel_calls.append({"account_id": account_id, "payload": payload})
        raise AssertionError("Unsupported subscription-cancel route must not call service.")

    def initiate_subscription_restart(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.subscription_restart_calls.append({"account_id": account_id, "payload": payload})
        raise AssertionError("Unsupported subscription-restart route must not call service.")

    def validate_promo_code(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.promo_validate_calls.append({"account_id": account_id, "payload": payload})
        raise AssertionError("Unsupported promo validate route must not call service.")

    def apply_promo_code(self, account_id: UUID, payload) -> BillingActionInitiationResponse:
        self.promo_apply_calls.append({"account_id": account_id, "payload": payload})
        raise AssertionError("Unsupported promo apply route must not call service.")


class StubRateLimiter:
    def __init__(self, *, reject: bool = False) -> None:
        self.reject = reject
        self.check_calls: list[dict[str, object]] = []

    def check(self, *, action: str, key: str, policy) -> None:  # noqa: ANN001
        self.check_calls.append(
            {
                "action": action,
                "key": key,
                "policy": policy,
            }
        )
        if self.reject:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")


def _build_context() -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="billing-user",
        email="billing-user@example.com",
        status="active",
        role="user",
        email_verified_at=now - timedelta(days=1),
        session_created_at=now - timedelta(hours=1),
        session_expires_at=now + timedelta(hours=1),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


@pytest.fixture()
def router_harness(monkeypatch: pytest.MonkeyPatch):
    context = _build_context()
    service = StubBillingSummaryService()
    rate_limiter = StubRateLimiter()
    audit_events: list[dict[str, object]] = []

    def capture_audit_event(
        audit_hook,  # noqa: ANN001
        *,
        request,  # noqa: ANN001
        action: str,
        outcome: str,
        account_id: UUID | None = None,
        metadata: dict[str, object | None] | None = None,
    ) -> None:
        del audit_hook, request
        audit_events.append(
            {
                "action": action,
                "outcome": outcome,
                "account_id": account_id,
                "metadata": metadata or {},
            }
        )

    monkeypatch.setattr(billing_router, "emit_audit_event", capture_audit_event)

    app = FastAPI()
    app.include_router(billing_router.router, prefix="/api/v1")
    app.dependency_overrides[require_authenticated_session_context] = lambda: context
    app.dependency_overrides[get_billing_summary_service] = lambda: service
    app.dependency_overrides[get_rate_limiter] = lambda: rate_limiter
    app.dependency_overrides[get_audit_hook] = lambda: object()

    with TestClient(app) as client:
        yield {
            "client": client,
            "context": context,
            "service": service,
            "rate_limiter": rate_limiter,
            "audit_events": audit_events,
            "app": app,
        }

    app.dependency_overrides.clear()


def test_billing_snapshot_delegates_to_authenticated_account(router_harness) -> None:  # noqa: ANN001
    client: TestClient = router_harness["client"]
    context: AuthenticatedSessionContext = router_harness["context"]
    service: StubBillingSummaryService = router_harness["service"]

    response = client.get("/api/v1/billing/snapshot")

    assert response.status_code == 200
    body = response.json()
    assert body["pay_integration_status"] == "available"
    assert body["pay_projection_billing"]["subscribed_products"][0]["product_code"] == "ZEPTA"
    assert body["pay_projection_billing"]["current_payment_method"]["last4"] == "4242"
    assert body["parent_billing_addresses"]["total_saved_count"] == 0
    assert service.snapshot_calls == [context.account_id]


def test_billing_read_routes_delegate_to_authenticated_account(router_harness) -> None:  # noqa: ANN001
    client: TestClient = router_harness["client"]
    context: AuthenticatedSessionContext = router_harness["context"]
    service: StubBillingSummaryService = router_harness["service"]

    subscriptions_response = client.get("/api/v1/billing/subscriptions")
    payment_methods_response = client.get("/api/v1/billing/payment-methods")
    transactions_response = client.get(
        "/api/v1/billing/transactions",
        params={"limit": 10, "cursor": "cursor-123"},
    )

    assert subscriptions_response.status_code == 200
    assert subscriptions_response.json()["pay_subscriptions"][0]["product_code"] == "ZEPTA"
    assert service.subscription_calls == [context.account_id]

    assert payment_methods_response.status_code == 200
    assert payment_methods_response.json()["pay_payment_methods"][0]["display_label"] == (
        "Visa ending in 4242"
    )
    assert service.payment_method_calls == [context.account_id]

    assert transactions_response.status_code == 200
    transaction_body = transactions_response.json()
    assert transaction_body["pay_transactions"]["items"][0]["product_code"] == "ZEPTA"
    assert transaction_body["pay_transactions"]["page"] == {
        "limit": 10,
        "cursor": "cursor-123",
        "next_cursor": None,
    }
    assert service.transaction_calls == [
        {
            "account_id": context.account_id,
            "limit": 10,
            "cursor": "cursor-123",
        }
    ]


def test_checkout_delegates_to_pay_service_and_emits_attempt_success_audit(router_harness) -> None:  # noqa: ANN001
    client: TestClient = router_harness["client"]
    context: AuthenticatedSessionContext = router_harness["context"]
    service: StubBillingSummaryService = router_harness["service"]
    rate_limiter: StubRateLimiter = router_harness["rate_limiter"]
    audit_events: list[dict[str, object]] = router_harness["audit_events"]

    payload = {
        "product_code": "ZEPTA",
        "plan_code": "zepta_lvl_1",
        "billing_interval": "month",
        "success_url": "https://app.example.test/billing/success",
        "cancel_url": "https://app.example.test/billing/cancel",
        "promo_code": "SAVE20",
    }

    response = client.post("/api/v1/billing/checkout", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Checkout initiated."
    assert body["action"] == "checkout"
    assert body["pay_result"] == {
        "pay_redirect_url": "https://pay.example.test/session/checkout_123",
        "pay_session_id": "checkout_123",
        "pay_client_secret": None,
    }

    assert len(service.checkout_calls) == 1
    checkout_call = service.checkout_calls[0]
    assert checkout_call["account_id"] == context.account_id
    assert checkout_call["payload"].product_code == "ZEPTA"
    assert checkout_call["payload"].plan_code == "zepta_lvl_1"
    assert checkout_call["payload"].billing_interval == "month"
    assert checkout_call["payload"].promo_code == "SAVE20"

    assert [call["action"] for call in rate_limiter.check_calls] == ["billing_checkout"]
    assert audit_events == [
        {
            "action": "billing.checkout",
            "outcome": "attempt",
            "account_id": context.account_id,
            "metadata": {
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
                "billing_interval": "month",
            },
        },
        {
            "action": "billing.checkout",
            "outcome": "success",
            "account_id": context.account_id,
            "metadata": {
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
                "billing_interval": "month",
            },
        },
    ]


@pytest.mark.parametrize(
    (
        "path",
        "payload",
        "expected_action",
        "expected_rate_limit_action",
        "expected_audit_action",
        "expected_metadata",
        "service_call_attribute",
    ),
    [
        (
            "/api/v1/billing/subscription-change",
            {
                "product_code": "ZEPTA",
                "target_plan_code": "zepta_lvl_2",
                "target_billing_interval": "month",
                "promo_code": "SAVE20",
            },
            "subscription_change",
            "billing_subscription_change",
            "billing.subscription_change",
            {
                "product_code": "ZEPTA",
                "target_plan_code": "zepta_lvl_2",
                "target_billing_interval": "month",
            },
            "subscription_change_calls",
        ),
        (
            "/api/v1/billing/subscription-cancel",
            {
                "product_code": "ZEPTA",
                "reason": "Too expensive",
            },
            "subscription_cancel",
            "billing_subscription_cancel",
            "billing.subscription_cancel",
            {
                "product_code": "ZEPTA",
                "reason_provided": True,
            },
            "subscription_cancel_calls",
        ),
        (
            "/api/v1/billing/subscription-restart",
            {
                "product_code": "ZEPTA",
                "reason": "Restarting service",
            },
            "subscription_restart",
            "billing_subscription_restart",
            "billing.subscription_restart",
            {
                "product_code": "ZEPTA",
                "reason_provided": True,
            },
            "subscription_restart_calls",
        ),
        (
            "/api/v1/billing/promo-code/validate",
            {
                "promo_code": "SAVE20",
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
            },
            "promo_code_validation",
            "billing_promo_validate",
            "billing.promo_validate",
            {
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
            },
            "promo_validate_calls",
        ),
        (
            "/api/v1/billing/promo-code/apply",
            {
                "promo_code": "SAVE20",
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
            },
            "promo_code_apply",
            "billing_promo_apply",
            "billing.promo_apply",
            {
                "product_code": "ZEPTA",
                "plan_code": "zepta_lvl_1",
            },
            "promo_apply_calls",
        ),
    ],
)
def test_unsupported_billing_actions_return_501_without_calling_pay_service(
    router_harness,  # noqa: ANN001
    path: str,
    payload: dict[str, object],
    expected_action: str,
    expected_rate_limit_action: str,
    expected_audit_action: str,
    expected_metadata: dict[str, object],
    service_call_attribute: str,
) -> None:
    client: TestClient = router_harness["client"]
    context: AuthenticatedSessionContext = router_harness["context"]
    service: StubBillingSummaryService = router_harness["service"]
    rate_limiter: StubRateLimiter = router_harness["rate_limiter"]
    audit_events: list[dict[str, object]] = router_harness["audit_events"]

    response = client.post(path, json=payload)

    assert response.status_code == 501
    assert response.json() == {
        "detail": {
            "code": "billing_action_not_supported",
            "action": expected_action,
            "message": f"Billing action '{expected_action}' is not supported by the Pay service yet.",
        }
    }

    assert getattr(service, service_call_attribute) == []
    assert [call["action"] for call in rate_limiter.check_calls] == [expected_rate_limit_action]
    assert audit_events == [
        {
            "action": expected_audit_action,
            "outcome": "attempt",
            "account_id": context.account_id,
            "metadata": expected_metadata,
        },
        {
            "action": expected_audit_action,
            "outcome": "unsupported",
            "account_id": context.account_id,
            "metadata": expected_metadata,
        },
    ]


def test_subscription_lifecycle_routes_reject_old_subscription_id_shape(router_harness) -> None:  # noqa: ANN001
    client: TestClient = router_harness["client"]
    service: StubBillingSummaryService = router_harness["service"]

    response = client.post(
        "/api/v1/billing/subscription-cancel",
        json={
            "subscription_id": "sub_123",
            "reason": "old payload shape",
        },
    )

    assert response.status_code == 422
    assert service.subscription_cancel_calls == []


def test_unsupported_billing_action_rate_limit_blocks_before_audit_and_service(
    router_harness,  # noqa: ANN001
) -> None:
    client: TestClient = router_harness["client"]
    service: StubBillingSummaryService = router_harness["service"]
    rate_limiter: StubRateLimiter = router_harness["rate_limiter"]
    audit_events: list[dict[str, object]] = router_harness["audit_events"]
    rate_limiter.reject = True

    response = client.post(
        "/api/v1/billing/promo-code/apply",
        json={
            "promo_code": "SAVE20",
            "product_code": "ZEPTA",
            "plan_code": "zepta_lvl_1",
        },
    )

    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded."}
    assert [call["action"] for call in rate_limiter.check_calls] == ["billing_promo_apply"]
    assert service.promo_apply_calls == []
    assert audit_events == []