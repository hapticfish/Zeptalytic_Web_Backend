from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.address_repository import AddressRepository
from app.integrations import PayClient, PayClientInvalidResponseError, PayClientUnavailableError
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingActionResult,
    BillingCheckoutInitiationRequest,
    BillingAddressBookSummary,
    BillingAddressSummary,
    BillingPaymentMethodSummary,
    BillingPaymentMethodsResponse,
    BillingPromoCodeRequest,
    BillingSnapshotPayProjectionSummary,
    BillingSnapshotResponse,
    BillingSubscriptionChangeRequest,
    BillingSubscriptionLifecycleRequest,
    BillingSubscriptionSummary,
    BillingSubscriptionsResponse,
    BillingTransactionSummary,
    BillingTransactionsPage,
    BillingTransactionsResponse,
)
from app.schemas.common import CursorPageInfo
from app.services.pay_projection_service import PayProjectionService

PRODUCT_NAMES = {
    "altra": "ALTRA",
    "zardbot": "ZardBot",
    "zepta": "Zepta",
}


class BillingActionUnavailableError(Exception):
    """Raised when a delegated billing action cannot reach Pay."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"Billing action '{action}' is unavailable.")


class BillingActionInvalidResponseError(Exception):
    """Raised when Pay returns an invalid delegated billing action payload."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"Billing action '{action}' returned an invalid response.")


class BillingSummaryService:
    def __init__(
        self,
        address_repository: AddressRepository,
        pay_projection_service: PayProjectionService,
        pay_client: PayClient | None = None,
    ) -> None:
        self._address_repository = address_repository
        self._pay_projection_service = pay_projection_service
        self._pay_client = pay_client

    def get_snapshot(self, account_id) -> BillingSnapshotResponse:  # noqa: ANN001
        snapshot = self._pay_projection_service.refresh_account_snapshot(account_id)
        subscriptions = self._build_subscription_summaries(snapshot.subscriptions, snapshot.payments)
        payment_methods = self._build_payment_method_summaries(snapshot.payment_methods)
        return BillingSnapshotResponse(
            pay_integration_status=snapshot.sync.pay_status,
            pay_projection_billing=BillingSnapshotPayProjectionSummary(
                subscribed_products=subscriptions,
                current_payment_method=payment_methods[0] if payment_methods else None,
            )
            if subscriptions or payment_methods
            else None,
            parent_billing_addresses=self._build_address_book(account_id),
        )

    def list_subscriptions(self, account_id) -> BillingSubscriptionsResponse:  # noqa: ANN001
        snapshot = self._pay_projection_service.refresh_account_snapshot(account_id)
        return BillingSubscriptionsResponse(
            pay_integration_status=snapshot.sync.pay_status,
            pay_subscriptions=self._build_subscription_summaries(snapshot.subscriptions, snapshot.payments),
        )

    def list_payment_methods(self, account_id) -> BillingPaymentMethodsResponse:  # noqa: ANN001
        snapshot = self._pay_projection_service.refresh_account_snapshot(account_id)
        return BillingPaymentMethodsResponse(
            pay_integration_status=snapshot.sync.pay_status,
            pay_payment_methods=self._build_payment_method_summaries(snapshot.payment_methods),
        )

    def list_transactions(
        self,
        account_id,  # noqa: ANN001
        *,
        limit: int = 25,
        cursor: str | None = None,
    ) -> BillingTransactionsResponse:
        snapshot = self._pay_projection_service.refresh_account_snapshot(account_id)
        transactions = [
            BillingTransactionSummary(
                source="pay_projection",
                occurred_at=payment.paid_at or payment.updated_at,
                description=self._build_transaction_description(payment.product_code, payment.payment_rail),
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                status=payment.normalized_status,
                product_code=payment.product_code,
            )
            for payment in snapshot.payments[:limit]
        ]
        next_cursor = None
        if len(snapshot.payments) > limit:
            next_cursor = snapshot.payments[limit - 1].updated_at.isoformat()

        return BillingTransactionsResponse(
            pay_integration_status=snapshot.sync.pay_status,
            pay_transactions=BillingTransactionsPage(
                items=transactions,
                page=CursorPageInfo(limit=limit, cursor=cursor, next_cursor=next_cursor),
            ),
        )

    def initiate_checkout(
        self,
        account_id,  # noqa: ANN001
        payload: BillingCheckoutInitiationRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="checkout",
            path=f"/internal/accounts/{account_id}/billing/checkout",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Checkout initiated.",
        )

    def initiate_subscription_change(
        self,
        account_id,  # noqa: ANN001
        payload: BillingSubscriptionChangeRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="subscription_change",
            path=f"/internal/accounts/{account_id}/billing/subscription-change",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Subscription change initiated.",
        )

    def initiate_subscription_cancel(
        self,
        account_id,  # noqa: ANN001
        payload: BillingSubscriptionLifecycleRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="subscription_cancel",
            path=f"/internal/accounts/{account_id}/billing/subscription-cancel",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Subscription cancellation initiated.",
        )

    def initiate_subscription_restart(
        self,
        account_id,  # noqa: ANN001
        payload: BillingSubscriptionLifecycleRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="subscription_restart",
            path=f"/internal/accounts/{account_id}/billing/subscription-restart",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Subscription restart initiated.",
        )

    def validate_promo_code(
        self,
        account_id,  # noqa: ANN001
        payload: BillingPromoCodeRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="promo_code_validation",
            path=f"/internal/accounts/{account_id}/billing/promo-code/validate",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Promo code validated.",
        )

    def apply_promo_code(
        self,
        account_id,  # noqa: ANN001
        payload: BillingPromoCodeRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="promo_code_apply",
            path=f"/internal/accounts/{account_id}/billing/promo-code/apply",
            payload=payload.model_dump(mode="json", exclude_none=True),
            message="Promo code applied.",
        )

    def _build_address_book(self, account_id) -> BillingAddressBookSummary:  # noqa: ANN001
        address_records = self._address_repository.list_addresses_for_account(account_id)
        return BillingAddressBookSummary(
            total_saved_count=len(address_records),
            addresses=[
                BillingAddressSummary(
                    address_id=record.address_id,
                    address_type=record.address_type,
                    label=record.label,
                    full_name=record.full_name,
                    formatted_address=record.formatted_address,
                    country_code=record.country_code,
                    is_primary=record.is_primary,
                )
                for record in address_records
            ],
        )

    @staticmethod
    def _build_subscription_summaries(subscriptions, payments):  # noqa: ANN001
        latest_payment_by_product = {}
        for payment in payments:
            if payment.product_code is None or payment.product_code in latest_payment_by_product:
                continue
            latest_payment_by_product[payment.product_code] = payment

        return [
            BillingSubscriptionSummary(
                source="pay_projection",
                product_code=subscription.product_code,
                product_name=PRODUCT_NAMES.get(
                    subscription.product_code,
                    subscription.product_code.replace("-", " ").title(),
                ),
                plan_code=subscription.plan_code,
                subscription_status=subscription.normalized_status,
                billing_interval=subscription.billing_interval,
                current_charge_amount_cents=None
                if latest_payment_by_product.get(subscription.product_code) is None
                else latest_payment_by_product[subscription.product_code].amount_cents,
                currency=None
                if latest_payment_by_product.get(subscription.product_code) is None
                else latest_payment_by_product[subscription.product_code].currency,
                next_payment_at=subscription.next_billing_at,
                cancel_at_period_end=subscription.cancel_at_period_end,
            )
            for subscription in subscriptions
        ]

    @staticmethod
    def _build_payment_method_summaries(payment_methods) -> list[BillingPaymentMethodSummary]:  # noqa: ANN001
        return [
            BillingPaymentMethodSummary(
                source="pay_projection",
                provider=payment_method.provider,
                method_type="card",
                display_label=f"{payment_method.brand.title()} ending in {payment_method.last4}",
                brand=payment_method.brand,
                last4=payment_method.last4,
                exp_month=payment_method.exp_month,
                exp_year=payment_method.exp_year,
                cardholder_name=payment_method.billing_name,
                billing_country=payment_method.billing_country,
                is_default=payment_method.is_default,
                status=payment_method.status,
            )
            for payment_method in payment_methods
        ]

    @staticmethod
    def _build_transaction_description(product_code: str | None, payment_rail: str) -> str:
        if product_code:
            product_name = PRODUCT_NAMES.get(product_code, product_code.replace("-", " ").title())
            return f"{product_name} payment via {payment_rail}"
        return f"Payment via {payment_rail}"

    def _initiate_action(
        self,
        *,
        account_id,  # noqa: ANN001
        action: str,
        path: str,
        payload: dict[str, object],
        message: str,
    ) -> BillingActionInitiationResponse:
        del account_id

        if self._pay_client is None:
            raise BillingActionUnavailableError(action)

        try:
            response_payload = self._pay_client.request_json(
                "POST",
                path,
                json_body=payload,
                expected_status_codes={200, 201, 202},
            )
        except PayClientUnavailableError as exc:
            raise BillingActionUnavailableError(action) from exc
        except PayClientInvalidResponseError as exc:
            raise BillingActionInvalidResponseError(action) from exc

        if not isinstance(response_payload, dict):
            raise BillingActionInvalidResponseError(action)

        pay_result = self._build_action_result(action, response_payload)
        return BillingActionInitiationResponse(
            message=message,
            action=action,
            pay_result=pay_result,
        )

    @staticmethod
    def _build_action_result(action: str, payload: dict[str, object]) -> BillingActionResult | None:
        safe_string_fields = {
            key: value
            for key in ("pay_redirect_url", "pay_session_id", "pay_client_secret")
            if (value := payload.get(key)) is not None
        }
        for value in safe_string_fields.values():
            if not isinstance(value, str):
                raise BillingActionInvalidResponseError(action)

        if not safe_string_fields:
            return None

        return BillingActionResult(**safe_string_fields)


def build_billing_summary_service(
    db: Session,
    pay_projection_service: PayProjectionService,
    pay_client: PayClient | None = None,
) -> BillingSummaryService:
    return BillingSummaryService(AddressRepository(db), pay_projection_service, pay_client)
