from __future__ import annotations

from dataclasses import dataclass

from app.schemas.launcher import (
    LauncherBlockingReason,
    LauncherPayProjectionSummary,
    LauncherProductSummary,
    LauncherProductsResponse,
)
from app.services.auth_service import AuthenticatedSessionContext
from app.services.pay_projection_service import (
    PayProjectionEntitlementSummary,
    PayProjectionProductAccessState,
    PayProjectionService,
    PayProjectionSnapshot,
)

PRODUCT_CODE_ALIASES = {
    "altra": "ALTRA",
    "zardbot": "ZARDBOT",
    "zard_bot": "ZARDBOT",
    "zepta": "ZEPTA",
}

PRODUCT_DISPLAY_METADATA = {
    "ALTRA": {"product_name": "ALTRA", "display_tag": "Digital Experience"},
    "ZARDBOT": {"product_name": "ZardBot", "display_tag": "Crypto Intelligence"},
    "ZEPTA": {"product_name": "Zepta", "display_tag": "Trading Bot"},
}

PRODUCT_DISPLAY_ORDER = {
    "ZEPTA": 10,
    "ZARDBOT": 20,
    "ALTRA": 30,
}

ACTIVE_ENTITLEMENT_STATUSES = {"active", "granted", "on"}


@dataclass(slots=True)
class LauncherProductDecision:
    access_state: str
    can_launch: bool
    launch_url: str | None
    blocked_reason: LauncherBlockingReason | None
    status_message: str | None


class LauncherService:
    def __init__(self, pay_projection_service: PayProjectionService) -> None:
        self._pay_projection_service = pay_projection_service

    def get_products(
        self,
        context: AuthenticatedSessionContext,
    ) -> LauncherProductsResponse:
        snapshot = self._pay_projection_service.refresh_account_snapshot(context.account_id)
        return self._build_products_response(context, snapshot)

    def _build_products_response(
        self,
        context: AuthenticatedSessionContext,
        snapshot: PayProjectionSnapshot,
    ) -> LauncherProductsResponse:
        entitlements_by_product = self._index_by_canonical_product(snapshot.entitlements)
        subscriptions_by_product = self._index_by_canonical_product(snapshot.subscriptions)
        access_states_by_product = self._index_by_canonical_product(snapshot.product_access_states)

        product_codes = sorted(
            set(PRODUCT_DISPLAY_METADATA)
            | set(entitlements_by_product)
            | set(subscriptions_by_product)
            | set(access_states_by_product),
            key=self._product_sort_key,
        )
        products = [
            self._build_product_summary(
                product_code=product_code,
                context=context,
                pay_status=snapshot.sync.pay_status,
                entitlement=entitlements_by_product.get(product_code),
                subscription=subscriptions_by_product.get(product_code),
                access_state=access_states_by_product.get(product_code),
            )
            for product_code in product_codes
        ]

        return LauncherProductsResponse(
            pay_integration_status=snapshot.sync.pay_status,
            products=products,
        )

    def _build_product_summary(
        self,
        *,
        product_code: str,
        context: AuthenticatedSessionContext,
        pay_status: str,
        entitlement: PayProjectionEntitlementSummary | None,
        subscription,
        access_state: PayProjectionProductAccessState | None,
    ) -> LauncherProductSummary:
        metadata = self._product_metadata(product_code)
        decision = self._decide_access(
            context=context,
            pay_status=pay_status,
            entitlement=entitlement,
            access_state=access_state,
        )

        return LauncherProductSummary(
            product_code=product_code,
            product_name=metadata["product_name"],
            display_tag=metadata["display_tag"],
            pay_projection=self._build_projection_summary(entitlement, subscription, access_state),
            access_state=decision.access_state,
            can_launch=decision.can_launch,
            launch_url=decision.launch_url,
            blocked_reason=decision.blocked_reason,
            status_message=decision.status_message,
        )

    @staticmethod
    def _build_projection_summary(
        entitlement: PayProjectionEntitlementSummary | None,
        subscription,
        access_state: PayProjectionProductAccessState | None,
    ) -> LauncherPayProjectionSummary | None:
        if entitlement is None and subscription is None and access_state is None:
            return None

        last_synced_at = next(
            (
                value
                for value in (
                    None if entitlement is None else entitlement.last_synced_at,
                    None if subscription is None else subscription.last_synced_at,
                    None if access_state is None else access_state.updated_at,
                )
                if value is not None
            ),
            None,
        )
        provisioning_state = None
        if access_state is not None and access_state.access_state == "provision_pending":
            provisioning_state = "pending"
        elif access_state is not None and access_state.access_state == "active":
            provisioning_state = "ready"

        return LauncherPayProjectionSummary(
            entitlement_status=None if entitlement is None else entitlement.status,
            subscription_status=None if subscription is None else subscription.normalized_status,
            product_access_state=None if access_state is None else access_state.access_state,
            provisioning_state=provisioning_state,
            last_synced_at=last_synced_at,
        )

    @staticmethod
    def _decide_access(
        *,
        context: AuthenticatedSessionContext,
        pay_status: str,
        entitlement: PayProjectionEntitlementSummary | None,
        access_state: PayProjectionProductAccessState | None,
    ) -> LauncherProductDecision:
        if context.status == "suspended":
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="account_suspended",
                    message="Your account is suspended. Billing and support remain available.",
                ),
                status_message="Billing and support remain available while launch access is blocked.",
            )

        if context.status != "active":
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="account_not_active",
                    message="Your account is not active yet.",
                ),
                status_message="Finish activating your account before launching products.",
            )

        if not context.is_email_verified:
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="email_verification_required",
                    message="Verify your email before launching products.",
                ),
                status_message="Email verification is required for launcher access.",
            )

        if pay_status == "unavailable":
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="pay_unavailable",
                    message="Launcher access is temporarily unavailable while subscription status is refreshing.",
                ),
                status_message="Pay-derived entitlement state is unavailable.",
            )

        entitlement_status = "" if entitlement is None else entitlement.status.lower()
        if entitlement is None or entitlement_status not in ACTIVE_ENTITLEMENT_STATUSES:
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="entitlement_inactive",
                    message="You do not have active entitlement for this product.",
                ),
                status_message="Subscribe to unlock launcher access.",
            )

        if access_state is None:
            return LauncherProductDecision(
                access_state="blocked",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="product_access_unavailable",
                    message="Product access details are still being prepared.",
                ),
                status_message="Product access is not ready yet.",
            )

        if access_state.access_state == "provision_pending":
            return LauncherProductDecision(
                access_state="provision_pending",
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="provision_pending",
                    message="Your subscription is active, but product setup is still being completed.",
                ),
                status_message="Provisioning is still in progress.",
            )

        if access_state.access_state != "active" or not access_state.launch_url:
            return LauncherProductDecision(
                access_state=access_state.access_state,
                can_launch=False,
                launch_url=None,
                blocked_reason=LauncherBlockingReason(
                    code="launch_blocked",
                    message=access_state.disabled_reason or "Product launch is currently unavailable.",
                ),
                status_message=access_state.disabled_reason,
            )

        return LauncherProductDecision(
            access_state="active",
            can_launch=True,
            launch_url=access_state.launch_url,
            blocked_reason=None,
            status_message="Ready to launch.",
        )

    @staticmethod
    def _index_by_canonical_product(items):  # noqa: ANN001
        indexed = {}
        for item in items:
            product_code = canonical_product_code(item.product_code)
            if not product_code:
                continue

            existing = indexed.get(product_code)
            if existing is None or item.product_code == product_code:
                indexed[product_code] = item

        return indexed

    @staticmethod
    def _product_metadata(product_code: str) -> dict[str, str | None]:
        metadata = PRODUCT_DISPLAY_METADATA.get(product_code)
        if metadata is not None:
            return metadata

        return {
            "product_name": product_code.replace("_", " ").replace("-", " ").title(),
            "display_tag": None,
        }

    @staticmethod
    def _product_sort_key(product_code: str) -> tuple[int, str]:
        return (PRODUCT_DISPLAY_ORDER.get(product_code, 999), product_code)


def canonical_product_code(product_code: str | None) -> str:
    if product_code is None:
        return ""

    normalized = product_code.strip()
    if not normalized:
        return ""

    alias_key = normalized.lower().replace("-", "_")
    return PRODUCT_CODE_ALIASES.get(alias_key, normalized.upper().replace("-", "_"))


def build_launcher_service(pay_projection_service: PayProjectionService) -> LauncherService:
    return LauncherService(pay_projection_service)