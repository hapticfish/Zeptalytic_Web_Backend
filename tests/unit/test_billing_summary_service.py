from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.address_repository import AddressRecord
from app.integrations import PayClientInvalidResponseError, PayClientUnavailableError
from app.schemas.billing import (
    BillingCheckoutInitiationRequest,
    BillingPromoCodeRequest,
    BillingSubscriptionChangeRequest,
    BillingSubscriptionLifecycleRequest,
)
from app.services.billing_summary_service import (
    BillingActionInvalidResponseError,
    BillingActionUnavailableError,
    BillingSummaryService,
)
from app.services.pay_projection_service import (
    PayProjectionPaymentMethodSummary,
    PayProjectionPaymentSummary,
    PayProjectionSnapshot,
    PayProjectionSubscriptionSummary,
    PayProjectionSyncMetadata,
)


class StubAddressRepository:
    def __init__(self, records: list[AddressRecord]) -> None:
        self._records = records
        self.requested_account_ids: list[object] = []

    def list_addresses_for_account(self, account_id):  # noqa: ANN001
        self.requested_account_ids.append(account_id)
        return list(self._records)


class StubPayProjectionService:
    def __init__(self, snapshot: PayProjectionSnapshot) -> None:
        self._snapshot = snapshot
        self.requested_account_ids: list[object] = []

    def refresh_account_snapshot(self, account_id):  # noqa: ANN001
        self.requested_account_ids.append(account_id)
        return self._snapshot


class StubPayClient:
    def __init__(self, *, payload=None, error: Exception | None = None) -> None:  # noqa: ANN001
        self._payload = payload
        self._error = error
        self.calls: list[dict[str, object]] = []

    def request_json(self, method: str, path: str, **kwargs):  # noqa: ANN001
        self.calls.append({"method": method, "path": path, **kwargs})
        if self._error is not None:
            raise self._error
        return self._payload


def _build_snapshot(*, pay_status: str = "available") -> PayProjectionSnapshot:
    synced_at = datetime(2026, 4, 18, 22, 0, tzinfo=timezone.utc)
    account_id = uuid4()
    return PayProjectionSnapshot(
        account_id=account_id,
        sync=PayProjectionSyncMetadata(pay_status=pay_status, refreshed_from_pay=pay_status == "available"),
        subscriptions=[
            PayProjectionSubscriptionSummary(
                product_code="zardbot",
                plan_code="starter-monthly",
                provider_subscription_id="sub_zardbot_product_001",
                provider_customer_reference="cus_zardbot_001",
                bundle_code=None,
                commercial_subject_type="product",
                commercial_subject_code="starter-monthly",
                billing_interval="monthly",
                normalized_status="active",
                provider_status_raw="active",
                current_period_start_at=synced_at,
                current_period_end_at=synced_at,
                cancel_at_period_end=False,
                canceled_at=None,
                next_billing_at=synced_at,
                last_synced_at=synced_at,
            )
        ],
        entitlements=[],
        payments=[
            PayProjectionPaymentSummary(
                product_code="zardbot",
                payment_rail="card",
                normalized_status="succeeded",
                amount_cents=4900,
                currency="USD",
                paid_at=synced_at,
                updated_at=synced_at,
            )
        ],
        payment_methods=[
            PayProjectionPaymentMethodSummary(
                provider="stripe",
                brand="visa",
                last4="4242",
                exp_month=12,
                exp_year=2030,
                billing_name="Billing User",
                billing_country="US",
                is_default=True,
                status="active",
                last_synced_at=synced_at,
            )
        ],
        product_access_states=[],
    )


def _build_address(account_id) -> AddressRecord:  # noqa: ANN001
    return AddressRecord(
        address_id=uuid4(),
        account_id=account_id,
        address_type="billing",
        label="Primary billing",
        full_name="Billing User",
        line1="100 Main Street",
        line2=None,
        city_or_locality="Chicago",
        state_or_region="IL",
        postal_code="60601",
        country_code="US",
        country_name="United States",
        formatted_address="100 Main Street, Chicago, IL 60601, US",
        is_primary=True,
        created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
    )


def test_billing_summary_service_builds_snapshot_from_projection_and_parent_addresses() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    service = BillingSummaryService(
        StubAddressRepository([_build_address(account_id)]),
        StubPayProjectionService(snapshot),
    )

    response = service.get_snapshot(account_id)

    assert response.pay_integration_status == "available"
    assert response.pay_projection_billing is not None
    assert response.pay_projection_billing.subscribed_products[0].product_name == "ZardBot"
    assert response.pay_projection_billing.current_payment_method is not None
    assert response.pay_projection_billing.current_payment_method.last4 == "4242"
    assert response.parent_billing_addresses.total_saved_count == 1


def test_billing_summary_service_returns_safe_empty_projection_sections_when_pay_is_unavailable() -> None:
    snapshot = _build_snapshot(pay_status="unavailable")
    snapshot.subscriptions = []
    snapshot.payments = []
    snapshot.payment_methods = []
    account_id = snapshot.account_id
    service = BillingSummaryService(
        StubAddressRepository([_build_address(account_id)]),
        StubPayProjectionService(snapshot),
    )

    response = service.get_snapshot(account_id)

    assert response.pay_integration_status == "unavailable"
    assert response.pay_projection_billing is None
    assert response.parent_billing_addresses.total_saved_count == 1


def test_billing_summary_service_builds_projection_backed_transactions_page() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
    )

    response = service.list_transactions(account_id, limit=25)

    assert response.pay_integration_status == "available"
    assert response.pay_transactions.items[0].description == "ZardBot payment via card"
    assert response.pay_transactions.page.limit == 25


def test_billing_summary_service_initiates_checkout_through_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "checkout",
            "status": "checkout_required",
            "message": "Checkout initiated.",
            "product_code": "zardbot",
            "plan_code": "starter-monthly",
            "billing_interval": "MONTHLY",
            "payment_rail": "STRIPE",
            "pay_result": {
                "pay_redirect_url": "https://pay.example/checkout/session_123",
                "pay_session_id": "session_123",
            },
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.initiate_checkout(
        account_id,
        BillingCheckoutInitiationRequest(
            product_code="zardbot",
            plan_code="starter-monthly",
            billing_interval="monthly",
            payment_rail="stripe",
            success_url="https://app.example/success",
            cancel_url="https://app.example/cancel",
        ),
    )

    assert response.action == "checkout"
    assert response.message == "Checkout initiated."
    assert response.pay_result is not None
    assert response.pay_result.status == "checkout_required"
    assert response.pay_result.product_code == "zardbot"
    assert response.pay_result.plan_code == "starter-monthly"
    assert response.pay_result.billing_interval == "MONTHLY"
    assert response.pay_result.payment_rail == "STRIPE"
    assert response.pay_result.pay_redirect_url == "https://pay.example/checkout/session_123"
    assert response.pay_result.pay_session_id == "session_123"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/checkout",
            "json_body": {
                "purchase_type": "product",
                "billing_interval": "MONTHLY",
                "payment_rail": "STRIPE",
                "product_code": "zardbot",
                "plan_code": "starter-monthly",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_initiates_bundle_checkout_through_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "checkout",
            "status": "checkout_required",
            "message": "Bundle checkout initiated.",
            "bundle_code": "pro_bundle",
            "billing_interval": "MONTHLY",
            "payment_rail": "STRIPE",
            "pay_result": {
                "pay_redirect_url": "https://pay.example/checkout/bundle_session_123",
                "pay_session_id": "bundle_session_123",
            },
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.initiate_checkout(
        account_id,
        BillingCheckoutInitiationRequest(
            purchase_type="bundle",
            bundle_code="pro_bundle",
            billing_interval="month",
            payment_rail="STRIPE",
            success_url="https://app.example/success",
            cancel_url="https://app.example/cancel",
        ),
    )

    assert response.action == "checkout"
    assert response.message == "Bundle checkout initiated."
    assert response.pay_result is not None
    assert response.pay_result.status == "checkout_required"
    assert response.pay_result.bundle_code == "pro_bundle"
    assert response.pay_result.pay_session_id == "bundle_session_123"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/checkout",
            "json_body": {
                "purchase_type": "bundle",
                "billing_interval": "MONTHLY",
                "payment_rail": "STRIPE",
                "bundle_code": "pro_bundle",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_delegates_subscription_change_to_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "subscription_change",
            "status": "checkout_required",
            "message": "Subscription upgrade requires checkout.",
            "product_code": "zardbot",
            "plan_code": "pro-monthly",
            "billing_interval": "MONTHLY",
            "payment_rail": "STRIPE",
            "pay_result": {
                "pay_redirect_url": "https://pay.example/checkout/upgrade_123",
                "pay_session_id": "upgrade_123",
            },
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.initiate_subscription_change(
        account_id,
        BillingSubscriptionChangeRequest(
            product_code="zardbot",
            target_plan_code="pro-monthly",
            target_billing_interval="monthly",
            payment_rail="stripe",
            success_url="https://app.example/success",
            cancel_url="https://app.example/cancel",
            promo_code="SAVE20",
        ),
    )

    assert response.action == "subscription_change"
    assert response.message == "Subscription upgrade requires checkout."
    assert response.pay_result is not None
    assert response.pay_result.status == "checkout_required"
    assert response.pay_result.pay_redirect_url == "https://pay.example/checkout/upgrade_123"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/subscription-change",
            "json_body": {
                "target_billing_interval": "MONTHLY",
                "product_code": "zardbot",
                "target_plan_code": "pro-monthly",
                "payment_rail": "STRIPE",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
                "promo_code": "SAVE20",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_delegates_subscription_cancel_to_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "subscription_cancel",
            "status": "scheduled",
            "message": "Subscription cancellation scheduled.",
            "product_code": "zardbot",
            "effective_at": "2026-07-01T00:00:00Z",
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.initiate_subscription_cancel(
        account_id,
        BillingSubscriptionLifecycleRequest(
            product_code="zardbot",
            reason="Too expensive",
            idempotency_key="cancel-123",
        ),
    )

    assert response.action == "subscription_cancel"
    assert response.message == "Subscription cancellation scheduled."
    assert response.pay_result is not None
    assert response.pay_result.status == "scheduled"
    assert response.pay_result.product_code == "zardbot"
    assert response.pay_result.effective_at is not None
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/subscription-cancel",
            "json_body": {
                "product_code": "zardbot",
                "reason": "Too expensive",
                "idempotency_key": "cancel-123",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_delegates_subscription_restart_to_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "subscription_restart",
            "status": "restarted",
            "message": "Subscription restarted.",
            "product_code": "zardbot",
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.initiate_subscription_restart(
        account_id,
        BillingSubscriptionLifecycleRequest(
            product_code="zardbot",
            reason="Restarting service",
        ),
    )

    assert response.action == "subscription_restart"
    assert response.message == "Subscription restarted."
    assert response.pay_result is not None
    assert response.pay_result.status == "restarted"
    assert response.pay_result.product_code == "zardbot"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/subscription-restart",
            "json_body": {
                "product_code": "zardbot",
                "reason": "Restarting service",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_delegates_promo_validate_to_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "valid": True,
            "promo_code": "save20",
            "normalized_code": "SAVE20",
            "message": "Promo code validated.",
            "product_code": "zardbot",
            "plan_code": "starter-monthly",
            "billing_interval": "MONTHLY",
            "payment_rail": "STRIPE",
            "discount_type": "PERCENT",
            "discount_percent": 20,
            "currency": "USD",
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.validate_promo_code(
        account_id,
        BillingPromoCodeRequest(
            promo_code="SAVE20",
            product_code="zardbot",
            plan_code="starter-monthly",
            billing_interval="month",
            payment_rail="stripe",
        ),
    )

    assert response.action == "promo_code_validation"
    assert response.message == "Promo code validated."
    assert response.pay_result is not None
    assert response.pay_result.valid is True
    assert response.pay_result.normalized_code == "SAVE20"
    assert response.pay_result.discount_type == "PERCENT"
    assert response.pay_result.discount_percent == 20
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/promo-code/validate",
            "json_body": {
                "promo_code": "SAVE20",
                "apply_mode": "CHECKOUT",
                "product_code": "zardbot",
                "plan_code": "starter-monthly",
                "billing_interval": "MONTHLY",
                "payment_rail": "STRIPE",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_delegates_promo_apply_to_pay_client() -> None:
    snapshot = _build_snapshot()
    account_id = snapshot.account_id
    pay_client = StubPayClient(
        payload={
            "action": "promo_code_apply",
            "status": "applied",
            "message": "Promo code applied.",
            "product_code": "zardbot",
            "plan_code": "starter-monthly",
            "billing_interval": "MONTHLY",
            "payment_rail": "STRIPE",
        }
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        pay_client,
    )

    response = service.apply_promo_code(
        account_id,
        BillingPromoCodeRequest(
            promo_code="SAVE20",
            product_code="zardbot",
            plan_code="starter-monthly",
            billing_interval="month",
            payment_rail="stripe",
            apply_mode="existing_subscription",
            idempotency_key="promo-123",
        ),
    )

    assert response.action == "promo_code_apply"
    assert response.message == "Promo code applied."
    assert response.pay_result is not None
    assert response.pay_result.status == "applied"
    assert response.pay_result.product_code == "zardbot"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/promo-code/apply",
            "json_body": {
                "promo_code": "SAVE20",
                "apply_mode": "EXISTING_SUBSCRIPTION",
                "product_code": "zardbot",
                "plan_code": "starter-monthly",
                "billing_interval": "MONTHLY",
                "payment_rail": "STRIPE",
                "idempotency_key": "promo-123",
            },
            "expected_status_codes": {200, 201, 202},
        }
    ]


def test_billing_summary_service_raises_unavailable_error_when_pay_action_cannot_reach_pay() -> None:
    snapshot = _build_snapshot()
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        StubPayClient(error=PayClientUnavailableError("Pay service is unavailable.")),
    )

    try:
        service.initiate_checkout(
            snapshot.account_id,
            BillingCheckoutInitiationRequest(
                product_code="zardbot",
                plan_code="starter-monthly",
                billing_interval="monthly",
                payment_rail="STRIPE",
                success_url="https://app.example/success",
                cancel_url="https://app.example/cancel",
            ),
        )
    except BillingActionUnavailableError as exc:
        assert exc.action == "checkout"
    else:
        raise AssertionError("Expected BillingActionUnavailableError")


def test_billing_summary_service_rejects_invalid_pay_action_payload() -> None:
    snapshot = _build_snapshot()
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        StubPayClient(error=PayClientInvalidResponseError("invalid")),
    )

    try:
        service.initiate_checkout(
            snapshot.account_id,
            BillingCheckoutInitiationRequest(
                product_code="zardbot",
                plan_code="starter-monthly",
                billing_interval="monthly",
                payment_rail="STRIPE",
                success_url="https://app.example/success",
                cancel_url="https://app.example/cancel",
            ),
        )
    except BillingActionInvalidResponseError as exc:
        assert exc.action == "checkout"
    else:
        raise AssertionError("Expected BillingActionInvalidResponseError")


def test_billing_summary_service_rejects_non_mapping_nested_pay_result() -> None:
    snapshot = _build_snapshot()
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
        StubPayClient(
            payload={
                "action": "checkout",
                "status": "checkout_required",
                "pay_result": "not-an-object",
            }
        ),
    )

    try:
        service.initiate_checkout(
            snapshot.account_id,
            BillingCheckoutInitiationRequest(
                product_code="zardbot",
                plan_code="starter-monthly",
                billing_interval="monthly",
                payment_rail="STRIPE",
                success_url="https://app.example/success",
                cancel_url="https://app.example/cancel",
            ),
        )
    except BillingActionInvalidResponseError as exc:
        assert exc.action == "checkout"
    else:
        raise AssertionError("Expected BillingActionInvalidResponseError")


def test_billing_summary_service_does_not_pair_product_only_payments_to_ambiguous_same_product_subscriptions() -> None:
    synced_at = datetime(2026, 4, 18, 22, 0, tzinfo=timezone.utc)
    account_id = uuid4()
    snapshot = PayProjectionSnapshot(
        account_id=account_id,
        sync=PayProjectionSyncMetadata(pay_status="available", refreshed_from_pay=True),
        subscriptions=[
            PayProjectionSubscriptionSummary(
                product_code="zardbot",
                plan_code="zardbot_analytics_pro",
                provider_subscription_id="sub_product_001",
                provider_customer_reference="cus_zardbot_001",
                bundle_code=None,
                commercial_subject_type="product",
                commercial_subject_code="zardbot_analytics_pro",
                billing_interval="monthly",
                normalized_status="active",
                provider_status_raw="active",
                current_period_start_at=synced_at,
                current_period_end_at=synced_at,
                cancel_at_period_end=False,
                canceled_at=None,
                next_billing_at=synced_at,
                last_synced_at=synced_at,
            ),
            PayProjectionSubscriptionSummary(
                product_code="zardbot",
                plan_code="BUNDLE_PRO",
                provider_subscription_id="sub_bundle_001",
                provider_customer_reference="cus_zardbot_001",
                bundle_code="bundle_pro",
                commercial_subject_type="bundle",
                commercial_subject_code="bundle_pro",
                billing_interval="monthly",
                normalized_status="active",
                provider_status_raw="active",
                current_period_start_at=synced_at,
                current_period_end_at=synced_at,
                cancel_at_period_end=False,
                canceled_at=None,
                next_billing_at=synced_at,
                last_synced_at=synced_at,
            ),
        ],
        entitlements=[],
        payments=[
            PayProjectionPaymentSummary(
                product_code="zardbot",
                payment_rail="card",
                normalized_status="succeeded",
                amount_cents=12000,
                currency="USD",
                paid_at=synced_at,
                updated_at=synced_at,
            )
        ],
        payment_methods=[],
        product_access_states=[],
    )
    service = BillingSummaryService(
        StubAddressRepository([]),
        StubPayProjectionService(snapshot),
    )

    response = service.list_subscriptions(account_id)

    assert len(response.pay_subscriptions) == 2

    product_subscription = next(
        item for item in response.pay_subscriptions if item.commercial_subject_type == "product"
    )
    bundle_subscription = next(
        item for item in response.pay_subscriptions if item.commercial_subject_type == "bundle"
    )

    assert product_subscription.plan_code == "zardbot_analytics_pro"
    assert product_subscription.commercial_subject_code == "zardbot_analytics_pro"
    assert product_subscription.current_charge_amount_cents is None
    assert product_subscription.currency is None

    assert bundle_subscription.plan_code == "BUNDLE_PRO"
    assert bundle_subscription.bundle_code == "bundle_pro"
    assert bundle_subscription.commercial_subject_code == "bundle_pro"
    assert bundle_subscription.current_charge_amount_cents is None
    assert bundle_subscription.currency is None
