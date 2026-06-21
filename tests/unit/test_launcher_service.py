from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.services.auth_service import AuthenticatedSessionContext
from app.services.launcher_service import LauncherService
from app.services.pay_projection_service import (
    PayProjectionEntitlementSummary,
    PayProjectionProductAccessState,
    PayProjectionSnapshot,
    PayProjectionSubscriptionSummary,
    PayProjectionSyncMetadata,
)


class StubPayProjectionService:
    def __init__(self, snapshot: PayProjectionSnapshot) -> None:
        self._snapshot = snapshot
        self.requested_account_ids: list[object] = []

    def refresh_account_snapshot(self, account_id):  # noqa: ANN001
        self.requested_account_ids.append(account_id)
        return self._snapshot


def _build_context(*, status: str = "active", email_verified: bool = True) -> AuthenticatedSessionContext:
    verified_at = datetime(2026, 4, 18, 23, 10, tzinfo=timezone.utc) if email_verified else None
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="launcher-user",
        email="launcher@example.com",
        status=status,
        role="user",
        email_verified_at=verified_at,
        session_created_at=datetime(2026, 4, 18, 22, 0, tzinfo=timezone.utc),
        session_expires_at=datetime(2026, 5, 18, 22, 0, tzinfo=timezone.utc),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


def _build_snapshot(*, pay_status: str = "available", access_state: str = "active") -> PayProjectionSnapshot:
    synced_at = datetime(2026, 4, 18, 23, 0, tzinfo=timezone.utc)
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
        entitlements=[
            PayProjectionEntitlementSummary(
                product_code="zardbot",
                plan_code="starter-monthly",
                status="active",
                starts_at=synced_at,
                ends_at=None,
                last_synced_at=synced_at,
            )
        ],
        payments=[],
        payment_methods=[],
        product_access_states=[
            PayProjectionProductAccessState(
                product_code="zardbot",
                access_state=access_state,
                launch_url="https://launcher.example.com/zardbot" if access_state == "active" else None,
                disabled_reason=None,
                updated_at=synced_at,
            )
        ],
    )


def test_launcher_service_returns_launchable_product_when_context_and_projection_allow_it() -> None:
    context = _build_context()
    projection = _build_snapshot()
    projection.account_id = context.account_id
    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    assert response.pay_integration_status == "available"
    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.can_launch is True
    assert zardbot.launch_url == "https://launcher.example.com/zardbot"
    assert zardbot.blocked_reason is None

def test_launcher_service_prefers_pay_product_access_state_over_stale_off_entitlement() -> None:
    context = _build_context()
    projection = _build_snapshot(access_state="active")
    projection.account_id = context.account_id

    projection.entitlements[0].status = "OFF"
    projection.product_access_states[0].access_state = "active"
    projection.product_access_states[0].launch_url = "https://launcher.example.com/zardbot"

    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.pay_projection is not None
    assert zardbot.pay_projection.entitlement_status == "OFF"
    assert zardbot.pay_projection.product_access_state == "active"
    assert zardbot.pay_projection.provisioning_state == "ready"
    assert zardbot.access_state == "active"
    assert zardbot.can_launch is True
    assert zardbot.launch_url == "https://launcher.example.com/zardbot"
    assert zardbot.blocked_reason is None


def test_launcher_service_omits_terminal_subscription_status_from_projection() -> None:
    context = _build_context()
    projection = _build_snapshot(access_state="inactive")
    projection.account_id = context.account_id

    projection.subscriptions[0].normalized_status = "canceled"
    projection.subscriptions[0].provider_status_raw = "canceled"
    projection.subscriptions[0].canceled_at = projection.subscriptions[0].last_synced_at

    projection.entitlements[0].status = "OFF"
    projection.product_access_states[0].access_state = "inactive"
    projection.product_access_states[0].launch_url = None
    projection.product_access_states[0].disabled_reason = None

    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.pay_projection is not None
    assert zardbot.pay_projection.subscription_status is None
    assert zardbot.pay_projection.entitlement_status == "OFF"
    assert zardbot.pay_projection.product_access_state == "inactive"
    assert zardbot.access_state == "inactive"
    assert zardbot.can_launch is False

def test_launcher_service_blocks_when_email_is_not_verified() -> None:
    context = _build_context(email_verified=False)
    projection = _build_snapshot()
    projection.account_id = context.account_id
    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.can_launch is False
    assert zardbot.blocked_reason is not None
    assert zardbot.blocked_reason.code == "email_verification_required"


def test_launcher_service_blocks_when_account_is_suspended() -> None:
    context = _build_context(status="suspended")
    projection = _build_snapshot()
    projection.account_id = context.account_id
    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.can_launch is False
    assert zardbot.blocked_reason is not None
    assert zardbot.blocked_reason.code == "account_suspended"


def test_launcher_service_blocks_when_pay_projection_is_unavailable() -> None:
    context = _build_context()
    projection = _build_snapshot(pay_status="unavailable")
    projection.account_id = context.account_id
    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert response.pay_integration_status == "unavailable"
    assert zardbot.can_launch is False
    assert zardbot.blocked_reason is not None
    assert zardbot.blocked_reason.code == "pay_unavailable"


def test_launcher_service_returns_pending_state_when_provisioning_is_not_finished() -> None:
    context = _build_context()
    projection = _build_snapshot(access_state="provision_pending")
    projection.account_id = context.account_id
    service = LauncherService(StubPayProjectionService(projection))

    response = service.get_products(context)

    zardbot = next(product for product in response.products if product.product_code == "ZARDBOT")
    assert zardbot.access_state == "provision_pending"
    assert zardbot.can_launch is False
    assert zardbot.blocked_reason is not None
    assert zardbot.blocked_reason.code == "provision_pending"
