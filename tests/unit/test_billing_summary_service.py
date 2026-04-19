from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.address_repository import AddressRecord
from app.integrations import PayClientInvalidResponseError, PayClientUnavailableError
from app.schemas.billing import BillingCheckoutInitiationRequest
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
            "pay_redirect_url": "https://pay.example/checkout/session_123",
            "pay_session_id": "session_123",
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
            success_url="https://app.example/success",
            cancel_url="https://app.example/cancel",
        ),
    )

    assert response.action == "checkout"
    assert response.message == "Checkout initiated."
    assert response.pay_result is not None
    assert response.pay_result.pay_redirect_url == "https://pay.example/checkout/session_123"
    assert response.pay_result.pay_session_id == "session_123"
    assert pay_client.calls == [
        {
            "method": "POST",
            "path": f"/internal/accounts/{account_id}/billing/checkout",
            "json_body": {
                "product_code": "zardbot",
                "plan_code": "starter-monthly",
                "billing_interval": "monthly",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
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
                success_url="https://app.example/success",
                cancel_url="https://app.example/cancel",
            ),
        )
    except BillingActionInvalidResponseError as exc:
        assert exc.action == "checkout"
    else:
        raise AssertionError("Expected BillingActionInvalidResponseError")
