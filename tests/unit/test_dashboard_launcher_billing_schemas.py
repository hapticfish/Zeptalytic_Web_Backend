from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import (
    BillingActionInitiationResponse,
    BillingAddressBookSummary,
    BillingAddressSummary,
    BillingCheckoutInitiationRequest,
    BillingPaymentMethodSummary,
    BillingSnapshotPayProjectionSummary,
    BillingSnapshotResponse,
    BillingSubscriptionSummary,
    BillingTransactionSummary,
    BillingTransactionsPage,
    BillingTransactionsResponse,
    CursorPageInfo,
    DashboardNotificationSummary,
    DashboardProgressSummary,
    DashboardSummaryResponse,
    DashboardSystemStatusSummary,
    LauncherBlockingReason,
    LauncherPayProjectionSummary,
    LauncherProductSummary,
    LauncherProductsResponse,
    MutationSuccessResponse,
)


def test_dashboard_launcher_billing_schema_exports_are_available() -> None:
    assert DashboardSummaryResponse is not None
    assert LauncherProductsResponse is not None
    assert BillingSnapshotResponse is not None
    assert BillingTransactionsResponse is not None
    assert BillingActionInitiationResponse is not None


def test_launcher_products_response_keeps_pay_projection_data_nested() -> None:
    response = LauncherProductsResponse(
        pay_integration_status="projection_only",
        products=[
            LauncherProductSummary(
                product_code="zardbot",
                product_name="ZardBot",
                pay_projection=LauncherPayProjectionSummary(
                    entitlement_status="active",
                    subscription_status="active",
                    product_access_state="provision_pending",
                    provisioning_state="pending",
                    last_synced_at=datetime(2026, 4, 18, 20, 0, tzinfo=timezone.utc),
                ),
                access_state="provision_pending",
                can_launch=False,
                blocked_reason=LauncherBlockingReason(
                    code="provision_pending",
                    message="Your subscription is active, but setup is still finishing.",
                ),
                status_message="Provisioning is still running.",
            )
        ],
    )

    assert response.model_dump(mode="json") == {
        "pay_integration_status": "projection_only",
        "products": [
            {
                "product_code": "zardbot",
                "product_name": "ZardBot",
                "display_tag": None,
                "pay_projection": {
                    "source": "pay_projection",
                    "entitlement_status": "active",
                    "subscription_status": "active",
                    "product_access_state": "provision_pending",
                    "provisioning_state": "pending",
                    "last_synced_at": "2026-04-18T20:00:00Z",
                },
                "access_state": "provision_pending",
                "can_launch": False,
                "launch_url": None,
                "blocked_reason": {
                    "code": "provision_pending",
                    "message": "Your subscription is active, but setup is still finishing.",
                },
                "status_message": "Provisioning is still running.",
            }
        ],
    }


def test_billing_snapshot_response_separates_parent_owned_and_pay_sections() -> None:
    snapshot = BillingSnapshotResponse(
        pay_integration_status="available",
        pay_projection_billing=BillingSnapshotPayProjectionSummary(
            subscribed_products=[
                BillingSubscriptionSummary(
                    source="pay_projection",
                    product_code="zepta",
                    product_name="Zepta",
                    plan_code="pro-monthly",
                    subscription_status="active",
                    billing_interval="monthly",
                    current_charge_amount_cents=4900,
                    currency="USD",
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
                exp_year=2027,
                cardholder_name="John Quinn",
                billing_country="US",
                is_default=True,
                status="active",
            ),
        ),
        parent_billing_addresses=BillingAddressBookSummary(
            total_saved_count=1,
            addresses=[
                BillingAddressSummary(
                    address_id=uuid4(),
                    address_type="billing",
                    label="Main billing",
                    full_name="John Quinn",
                    formatted_address="123 Main St, Chicago, IL 60601, USA",
                    country_code="US",
                    is_primary=True,
                )
            ],
        ),
    )

    payload = snapshot.model_dump(mode="json")

    assert "pay_projection_billing" in payload
    assert "parent_billing_addresses" in payload
    assert "provider_payment_method_id" not in str(payload)
    assert "provider_customer_id" not in str(payload)
    assert "external_account_reference" not in str(payload)


def test_billing_transactions_response_reuses_cursor_page_contract() -> None:
    response = BillingTransactionsResponse(
        pay_integration_status="available",
        pay_transactions=BillingTransactionsPage(
            items=[
                BillingTransactionSummary(
                    source="pay_live",
                    occurred_at=datetime(2026, 4, 18, 18, 30, tzinfo=timezone.utc),
                    description="Zepta Pro monthly renewal",
                    amount_cents=4900,
                    currency="USD",
                    status="paid",
                    product_code="zepta",
                )
            ],
            page=CursorPageInfo(limit=25, cursor="txn_001", next_cursor="txn_002"),
        ),
    )

    assert response.model_dump(mode="json") == {
        "pay_integration_status": "available",
        "pay_transactions": {
            "items": [
                {
                    "source": "pay_live",
                    "occurred_at": "2026-04-18T18:30:00Z",
                    "description": "Zepta Pro monthly renewal",
                    "amount_cents": 4900,
                    "currency": "USD",
                    "status": "paid",
                    "product_code": "zepta",
                }
            ],
            "page": {
                "limit": 25,
                "cursor": "txn_001",
                "next_cursor": "txn_002",
            },
        },
    }


def test_billing_action_response_reuses_standard_mutation_success_contract() -> None:
    response = BillingActionInitiationResponse(
        message="Checkout initiated.",
        action="checkout",
        pay_result={"pay_redirect_url": "https://pay.example/checkout/session_001"},
    )

    assert isinstance(response, MutationSuccessResponse)
    assert response.model_dump(mode="json") == {
        "success": True,
        "message": "Checkout initiated.",
        "action": "checkout",
        "pay_result": {
            "pay_redirect_url": "https://pay.example/checkout/session_001",
            "pay_session_id": None,
            "pay_client_secret": None,
        },
    }


def test_billing_checkout_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        BillingCheckoutInitiationRequest.model_validate(
            {
                "product_code": "zardbot",
                "plan_code": "pro-monthly",
                "billing_interval": "monthly",
                "success_url": "https://app.example/success",
                "cancel_url": "https://app.example/cancel",
                "provider_payment_method_id": "pm_should_not_be_here",
            }
        )


def test_dashboard_summary_response_groups_page_sections_with_owned_sources() -> None:
    response = DashboardSummaryResponse(
        launcher=LauncherProductsResponse(pay_integration_status="unavailable", products=[]),
        billing=BillingSnapshotResponse(
            pay_integration_status="unavailable",
            pay_projection_billing=None,
            parent_billing_addresses=BillingAddressBookSummary(total_saved_count=0, addresses=[]),
        ),
        parent_rewards_progress=DashboardProgressSummary(
            current_points=125,
            current_tier="BRONZE",
            current_milestone="100_points",
            next_milestone="200_points",
            points_to_next_milestone=75,
        ),
        parent_system_statuses=[
            DashboardSystemStatusSummary(
                product_code="zardbot",
                product_name="ZardBot",
                status="operational",
            )
        ],
        parent_notifications=[
            DashboardNotificationSummary(
                notification_type="announcement",
                title="Launcher maintenance window",
                published_at=datetime(2026, 4, 18, 21, 15, tzinfo=timezone.utc),
            )
        ],
    )

    payload = response.model_dump(mode="json")

    assert payload["parent_rewards_progress"]["source"] == "parent_owned"
    assert payload["parent_system_statuses"][0]["source"] == "parent_owned"
    assert payload["parent_notifications"][0]["source"] == "parent_owned"
