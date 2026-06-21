from __future__ import annotations

from collections.abc import Mapping

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.repositories.address_repository import AddressRepository
from app.integrations import PayClient, PayClientInvalidResponseError, PayClientUnavailableError
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingActionResult,
    BillingAddressBookSummary,
    BillingAddressSummary,
    BillingCheckoutInitiationRequest,
    BillingPaymentMethodSetupRequest,
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

PRODUCT_CODE_ALIASES = {
    "altra": "ALTRA",
    "zardbot": "ZARDBOT",
    "zard_bot": "ZARDBOT",
    "zepta": "ZEPTA",
}

PRODUCT_NAMES = {
    "ALTRA": "ALTRA",
    "ZARDBOT": "ZardBot",
    "ZEPTA": "Zepta",
}

_PAY_DOMAIN_ERROR_STATUS_CODES = {400, 404, 409, 422}

TERMINAL_SUBSCRIPTION_STATUSES = {
    "canceled",
    "cancelled",
    "ended",
    "expired",
}


class BillingActionUnavailableError(Exception):
    """Raised when a delegated billing action cannot reach Pay."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"Billing action '{action}' is unavailable.")


class BillingActionRejectedError(Exception):
    """Raised when Pay cleanly rejects a delegated billing action request."""

    def __init__(
        self,
        action: str,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self.action = action
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = dict(details or {})
        super().__init__(message)


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
            self._build_transaction_summary(payment)
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
            payload=self._build_checkout_payload(payload),
            default_message="Checkout initiated.",
        )

    def initiate_payment_method_setup(
        self,
        account_id,  # noqa: ANN001
        payload: BillingPaymentMethodSetupRequest,
    ) -> BillingActionInitiationResponse:
        return self._initiate_action(
            account_id=account_id,
            action="payment_method_setup",
            path="/api/payment-methods/setup-session",
            payload=self._build_payment_method_setup_payload(payload),
            default_message="Payment method setup initiated.",
            pay_scope="pay:payment_methods",
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
            payload=self._build_subscription_change_payload(payload),
            default_message="Subscription change initiated.",
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
            payload=self._build_subscription_lifecycle_payload(payload),
            default_message="Subscription cancellation initiated.",
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
            payload=self._build_subscription_lifecycle_payload(payload),
            default_message="Subscription restart initiated.",
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
            payload=self._build_promo_validate_payload(payload),
            default_message="Promo code validated.",
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
            payload=self._build_promo_apply_payload(payload),
            default_message="Promo code applied.",
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
        current_subscriptions = [
            subscription
            for subscription in subscriptions
            if BillingSummaryService._is_current_subscription_summary(subscription)
        ]

        latest_payment_by_product = {}
        for payment in payments:
            product_code = canonical_product_code(payment.product_code)
            if not product_code or product_code in latest_payment_by_product:
                continue
            latest_payment_by_product[product_code] = payment

        subscription_count_by_product: dict[str, int] = {}
        for subscription in current_subscriptions:
            product_code = canonical_product_code(subscription.product_code)
            if not product_code:
                continue
            subscription_count_by_product[product_code] = subscription_count_by_product.get(product_code, 0) + 1

        summaries = []
        for subscription in current_subscriptions:
            product_code = canonical_product_code(subscription.product_code)
            latest_payment = BillingSummaryService._safe_latest_payment_for_subscription(
                subscription=subscription,
                latest_payment=latest_payment_by_product.get(product_code),
                same_product_subscription_count=subscription_count_by_product.get(product_code, 0),
            )

            summaries.append(
                BillingSubscriptionSummary(
                    source="pay_projection",
                    product_code=product_code,
                    product_name=display_product_name(product_code),
                    plan_code=subscription.plan_code,
                    bundle_code=optional_text(getattr(subscription, "bundle_code", None)),
                    commercial_subject_type=optional_text(getattr(subscription, "commercial_subject_type", None)),
                    commercial_subject_code=optional_text(getattr(subscription, "commercial_subject_code", None)),
                    subscription_status=subscription.normalized_status,
                    billing_interval=subscription.billing_interval,
                    current_charge_amount_cents=None
                    if latest_payment is None
                    else latest_payment.amount_cents,
                    currency=None if latest_payment is None else latest_payment.currency,
                    next_payment_at=subscription.next_billing_at,
                    cancel_at_period_end=subscription.cancel_at_period_end,
                )
            )

        return summaries

    @staticmethod
    def _is_current_subscription_summary(subscription) -> bool:  # noqa: ANN001
        normalized_status = optional_text(getattr(subscription, "normalized_status", None))
        if normalized_status is None:
            return True

        return normalized_status.lower() not in TERMINAL_SUBSCRIPTION_STATUSES

    @staticmethod
    def _safe_latest_payment_for_subscription(
        *,
        subscription,  # noqa: ANN001
        latest_payment,  # noqa: ANN001
        same_product_subscription_count: int,
    ):  # noqa: ANN001
        if latest_payment is None:
            return None

        subscription_provider_subscription_id = optional_text(
            getattr(subscription, "provider_subscription_id", None)
        )
        payment_provider_subscription_id = optional_text(
            getattr(latest_payment, "provider_subscription_id", None)
        )
        if (
            subscription_provider_subscription_id is not None
            and payment_provider_subscription_id is not None
            and subscription_provider_subscription_id == payment_provider_subscription_id
        ):
            return latest_payment

        subscription_subject_type = optional_text(
            getattr(subscription, "commercial_subject_type", None)
        )
        subscription_subject_code = optional_text(
            getattr(subscription, "commercial_subject_code", None)
        )
        payment_subject_type = optional_text(getattr(latest_payment, "commercial_subject_type", None))
        payment_subject_code = optional_text(getattr(latest_payment, "commercial_subject_code", None))
        if (
            subscription_subject_type is not None
            and subscription_subject_code is not None
            and payment_subject_type is not None
            and payment_subject_code is not None
            and subscription_subject_type == payment_subject_type
            and subscription_subject_code == payment_subject_code
        ):
            return latest_payment

        if same_product_subscription_count <= 1:
            return latest_payment

        return None

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
    def _build_transaction_summary(payment) -> BillingTransactionSummary:  # noqa: ANN001
        product_code = canonical_product_code(payment.product_code)
        return BillingTransactionSummary(
            source="pay_projection",
            occurred_at=payment.paid_at or payment.updated_at,
            description=BillingSummaryService._build_transaction_description(
                product_code,
                payment.payment_rail,
            ),
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            status=payment.normalized_status,
            product_code=product_code or None,
        )

    @staticmethod
    def _build_transaction_description(product_code: str | None, payment_rail: str) -> str:
        if product_code:
            return f"{display_product_name(product_code)} payment via {payment_rail}"
        return f"Payment via {payment_rail}"

    def _initiate_action(
        self,
        *,
        account_id,  # noqa: ANN001
        action: str,
        path: str,
        payload: dict[str, object],
        default_message: str,
        pay_scope: str | None = None,
    ) -> BillingActionInitiationResponse:
        if self._pay_client is None:
            raise BillingActionUnavailableError(action)

        request_kwargs: dict[str, object] = {}
        if pay_scope is not None:
            request_kwargs["account_id"] = account_id
            request_kwargs["scope"] = pay_scope

        try:
            response_payload = self._pay_client.request_json(
                "POST",
                path,
                json_body=payload,
                expected_status_codes={200, 201, 202},
                **request_kwargs,
            )
        except PayClientUnavailableError as exc:
            raise BillingActionUnavailableError(action) from exc
        except PayClientInvalidResponseError as exc:
            if exc.status_code in _PAY_DOMAIN_ERROR_STATUS_CODES:
                raise self._build_action_rejected_error(action, exc) from exc
            raise BillingActionInvalidResponseError(action) from exc

        if not isinstance(response_payload, dict):
            raise BillingActionInvalidResponseError(action)

        pay_result = self._build_action_result(action, response_payload)
        return BillingActionInitiationResponse(
            message=self._build_action_message(response_payload, default_message),
            action=action,
            pay_result=pay_result,
        )

    @staticmethod
    def _build_checkout_payload(payload: BillingCheckoutInitiationRequest) -> dict[str, object]:
        purchase_type = payload.purchase_type or ("bundle" if payload.bundle_code else "product")
        result: dict[str, object] = {
            "purchase_type": purchase_type,
            "billing_interval": payload.billing_interval,
            "payment_rail": payload.payment_rail,
        }

        if purchase_type == "bundle":
            BillingSummaryService._copy_optional(result, "bundle_code", payload.bundle_code)
        else:
            BillingSummaryService._copy_optional(result, "product_code", payload.product_code)
            BillingSummaryService._copy_optional(result, "plan_code", payload.plan_code)

        BillingSummaryService._copy_optional(result, "success_url", payload.success_url)
        BillingSummaryService._copy_optional(result, "cancel_url", payload.cancel_url)
        BillingSummaryService._copy_optional(result, "promo_code", payload.promo_code)
        BillingSummaryService._copy_optional(result, "idempotency_key", payload.idempotency_key)

        return result

    @staticmethod
    def _build_payment_method_setup_payload(payload: BillingPaymentMethodSetupRequest) -> dict[str, object]:
        result: dict[str, object] = {
            "success_url": payload.success_url,
            "cancel_url": payload.cancel_url,
        }

        BillingSummaryService._copy_optional(result, "idempotency_key", payload.idempotency_key)
        BillingSummaryService._copy_optional(result, "customer_email", payload.customer_email)
        BillingSummaryService._copy_optional(result, "customer_name", payload.customer_name)
        if payload.metadata is not None:
            result["metadata"] = dict(payload.metadata)

        return result

    @staticmethod
    def _build_subscription_change_payload(payload: BillingSubscriptionChangeRequest) -> dict[str, object]:
        result: dict[str, object] = {
            "target_billing_interval": payload.target_billing_interval,
        }

        BillingSummaryService._copy_optional(result, "product_code", payload.product_code)
        BillingSummaryService._copy_optional(result, "bundle_code", payload.bundle_code)
        BillingSummaryService._copy_optional(result, "target_plan_code", payload.target_plan_code)
        BillingSummaryService._copy_optional(result, "target_bundle_code", payload.target_bundle_code)
        BillingSummaryService._copy_optional(result, "payment_rail", payload.payment_rail)
        BillingSummaryService._copy_optional(result, "success_url", payload.success_url)
        BillingSummaryService._copy_optional(result, "cancel_url", payload.cancel_url)
        BillingSummaryService._copy_optional(result, "promo_code", payload.promo_code)
        BillingSummaryService._copy_optional(result, "idempotency_key", payload.idempotency_key)

        return result

    @staticmethod
    def _build_subscription_lifecycle_payload(payload: BillingSubscriptionLifecycleRequest) -> dict[str, object]:
        result: dict[str, object] = {}

        BillingSummaryService._copy_optional(result, "product_code", payload.product_code)
        BillingSummaryService._copy_optional(result, "bundle_code", payload.bundle_code)
        BillingSummaryService._copy_optional(result, "reason", payload.reason)
        BillingSummaryService._copy_optional(result, "idempotency_key", payload.idempotency_key)

        return result

    @staticmethod
    def _build_promo_validate_payload(payload: BillingPromoCodeRequest) -> dict[str, object]:
        result: dict[str, object] = {
            "promo_code": payload.promo_code,
            "apply_mode": payload.apply_mode,
        }

        BillingSummaryService._copy_optional(result, "product_code", payload.product_code)
        BillingSummaryService._copy_optional(result, "bundle_code", payload.bundle_code)
        BillingSummaryService._copy_optional(result, "plan_code", payload.plan_code)
        BillingSummaryService._copy_optional(result, "billing_interval", payload.billing_interval)
        BillingSummaryService._copy_optional(result, "payment_rail", payload.payment_rail)

        return result

    @staticmethod
    def _build_promo_apply_payload(payload: BillingPromoCodeRequest) -> dict[str, object]:
        result = BillingSummaryService._build_promo_validate_payload(payload)
        BillingSummaryService._copy_optional(result, "idempotency_key", payload.idempotency_key)
        return result

    @staticmethod
    def _copy_optional(result: dict[str, object], key: str, value: object | None) -> None:
        if value is not None:
            result[key] = value

    @staticmethod
    def _build_action_message(payload: dict[str, object], default_message: str) -> str:
        message = payload.get("message")
        return message if isinstance(message, str) and message.strip() else default_message

    @staticmethod
    def _build_action_result(action: str, payload: dict[str, object]) -> BillingActionResult | None:
        nested_pay_result = payload.get("pay_result")
        sources: list[Mapping[str, object]] = [payload]

        if nested_pay_result is not None:
            if not isinstance(nested_pay_result, Mapping):
                raise BillingActionInvalidResponseError(action)
            sources.append(nested_pay_result)

        result_fields = (
            "status",
            "pay_redirect_url",
            "pay_session_id",
            "pay_client_secret",
            "provider",
            "provider_customer_id",
            "created_customer",
            "product_code",
            "bundle_code",
            "plan_code",
            "billing_interval",
            "payment_rail",
            "effective_at",
            "valid",
            "promo_code",
            "normalized_code",
            "discount_type",
            "discount_percent",
            "discount_amount_cents",
            "discount_months",
            "currency",
            "expires_at",
        )

        result_data: dict[str, object] = {}
        for source in sources:
            for field_name in result_fields:
                value = source.get(field_name)
                if value is not None:
                    result_data[field_name] = value

            checkout_url = source.get("checkout_url")
            if checkout_url is not None and "pay_redirect_url" not in result_data:
                result_data["pay_redirect_url"] = checkout_url

            session_id = source.get("session_id")
            if session_id is not None and "pay_session_id" not in result_data:
                result_data["pay_session_id"] = session_id

        if not result_data:
            return None

        try:
            return BillingActionResult(**result_data)
        except ValidationError as exc:
            raise BillingActionInvalidResponseError(action) from exc

    @staticmethod
    def _build_action_rejected_error(
        action: str,
        exc: PayClientInvalidResponseError,
    ) -> BillingActionRejectedError:
        status_code = exc.status_code or 400
        code = "billing_action_rejected"
        message = "Billing action request was rejected."
        details: dict[str, object] = {"action": action}

        response_body = exc.response_body
        if isinstance(response_body, Mapping):
            detail = response_body.get("detail")
            if isinstance(detail, Mapping):
                raw_code = detail.get("code")
                raw_message = detail.get("message")

                if isinstance(raw_code, str) and raw_code.strip():
                    code = raw_code.strip().lower()
                    details["pay_error_code"] = raw_code.strip()

                if isinstance(raw_message, str) and raw_message.strip():
                    message = raw_message.strip()

                for key, value in detail.items():
                    if key not in {"code", "message"}:
                        details[str(key)] = value
            elif isinstance(detail, str) and detail.strip():
                message = detail.strip()
            else:
                details["pay_response"] = dict(response_body)
        elif response_body is not None:
            details["pay_response"] = response_body

        return BillingActionRejectedError(
            action=action,
            status_code=status_code,
            code=code,
            message=message,
            details=details,
        )


def canonical_product_code(product_code: str | None) -> str:
    if product_code is None:
        return ""

    normalized = product_code.strip()
    if not normalized:
        return ""

    alias_key = normalized.lower().replace("-", "_")
    return PRODUCT_CODE_ALIASES.get(alias_key, normalized.upper().replace("-", "_"))


def optional_text(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def display_product_name(product_code: str | None) -> str:
    canonical_code = canonical_product_code(product_code)
    if not canonical_code:
        return "Unknown Product"

    return PRODUCT_NAMES.get(
        canonical_code,
        canonical_code.replace("_", " ").replace("-", " ").title(),
    )


def build_billing_summary_service(
    db: Session,
    pay_projection_service: PayProjectionService,
    pay_client: PayClient | None = None,
) -> BillingSummaryService:
    return BillingSummaryService(AddressRepository(db), pay_projection_service, pay_client)