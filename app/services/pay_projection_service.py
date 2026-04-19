from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.pay_projection_repository import (
    EntitlementSummaryRecord,
    PayProjectionRepository,
    PaymentMethodSummaryRecord,
    PaymentSummaryRecord,
    ProductAccessStateRecord,
    SubscriptionSummaryRecord,
)
from app.integrations import (
    PayClient,
    PayClientInvalidResponseError,
    PayClientUnavailableError,
)


@dataclass(slots=True)
class PayProjectionSyncMetadata:
    pay_status: str
    refreshed_from_pay: bool


@dataclass(slots=True)
class PayProjectionSubscriptionSummary:
    product_code: str
    plan_code: str
    billing_interval: str
    normalized_status: str
    provider_status_raw: str
    current_period_start_at: datetime | None
    current_period_end_at: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    next_billing_at: datetime | None
    last_synced_at: datetime


@dataclass(slots=True)
class PayProjectionEntitlementSummary:
    product_code: str
    plan_code: str
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    last_synced_at: datetime


@dataclass(slots=True)
class PayProjectionPaymentSummary:
    product_code: str | None
    payment_rail: str
    normalized_status: str
    amount_cents: int
    currency: str
    paid_at: datetime | None
    updated_at: datetime


@dataclass(slots=True)
class PayProjectionPaymentMethodSummary:
    provider: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    billing_name: str | None
    billing_country: str | None
    is_default: bool
    status: str
    last_synced_at: datetime


@dataclass(slots=True)
class PayProjectionProductAccessState:
    product_code: str
    access_state: str
    launch_url: str | None
    disabled_reason: str | None
    updated_at: datetime


@dataclass(slots=True)
class PayProjectionSnapshot:
    account_id: UUID
    sync: PayProjectionSyncMetadata
    subscriptions: list[PayProjectionSubscriptionSummary]
    entitlements: list[PayProjectionEntitlementSummary]
    payments: list[PayProjectionPaymentSummary]
    payment_methods: list[PayProjectionPaymentMethodSummary]
    product_access_states: list[PayProjectionProductAccessState]


class PayProjectionService:
    def __init__(
        self,
        repository: PayProjectionRepository,
        pay_client: PayClient,
    ) -> None:
        self._repository = repository
        self._pay_client = pay_client

    def get_cached_snapshot(self, account_id: UUID) -> PayProjectionSnapshot:
        return self._build_snapshot(
            account_id,
            pay_status="projection_only",
            refreshed_from_pay=False,
        )

    def refresh_account_snapshot(self, account_id: UUID) -> PayProjectionSnapshot:
        try:
            payload = self._pay_client.request_json(
                "GET",
                f"/internal/accounts/{account_id}/projection-summary",
            )
            projection_payload = self._normalize_projection_payload(payload)
            self._upsert_projection_payload(account_id, projection_payload)
            self._repository.commit()
        except (PayClientUnavailableError, PayClientInvalidResponseError):
            self._repository.rollback()
            return self._build_snapshot(
                account_id,
                pay_status="unavailable",
                refreshed_from_pay=False,
            )
        except Exception:
            self._repository.rollback()
            raise

        return self._build_snapshot(
            account_id,
            pay_status="available",
            refreshed_from_pay=True,
        )

    def _upsert_projection_payload(
        self,
        account_id: UUID,
        payload: Mapping[str, list[Mapping[str, Any]]],
    ) -> None:
        for subscription in payload["subscriptions"]:
            self._repository.upsert_subscription_summary(
                account_id,
                product_code=str(subscription["product_code"]),
                summary_data={
                    "plan_code": str(subscription["plan_code"]),
                    "billing_interval": str(subscription["billing_interval"]),
                    "normalized_status": str(subscription["normalized_status"]),
                    "provider_status_raw": str(subscription["provider_status_raw"]),
                    "current_period_start_at": subscription["current_period_start_at"],
                    "current_period_end_at": subscription["current_period_end_at"],
                    "cancel_at_period_end": bool(subscription["cancel_at_period_end"]),
                    "canceled_at": subscription["canceled_at"],
                    "next_billing_at": subscription["next_billing_at"],
                    "last_synced_at": subscription["last_synced_at"],
                },
            )

        for entitlement in payload["entitlements"]:
            self._repository.upsert_entitlement_summary(
                account_id,
                product_code=str(entitlement["product_code"]),
                summary_data={
                    "plan_code": str(entitlement["plan_code"]),
                    "status": str(entitlement["status"]),
                    "starts_at": entitlement["starts_at"],
                    "ends_at": entitlement["ends_at"],
                    "entitlement_metadata": dict(entitlement["entitlement_metadata"]),
                    "last_synced_at": entitlement["last_synced_at"],
                },
            )

        for payment in payload["payments"]:
            self._repository.upsert_payment_summary(
                account_id,
                summary_data={
                    "product_code": payment["product_code"],
                    "payment_rail": str(payment["payment_rail"]),
                    "normalized_status": str(payment["normalized_status"]),
                    "provider_status_raw": payment["provider_status_raw"],
                    "amount_cents": int(payment["amount_cents"]),
                    "currency": str(payment["currency"]),
                    "paid_at": payment["paid_at"],
                    "provider_payment_reference": payment["provider_payment_reference"],
                },
            )

        for payment_method in payload["payment_methods"]:
            self._repository.upsert_payment_method_summary(
                account_id,
                provider=str(payment_method["provider"]),
                provider_payment_method_id=str(payment_method["provider_payment_method_id"]),
                summary_data={
                    "provider_customer_id": str(payment_method["provider_customer_id"]),
                    "brand": str(payment_method["brand"]),
                    "last4": str(payment_method["last4"]),
                    "exp_month": int(payment_method["exp_month"]),
                    "exp_year": int(payment_method["exp_year"]),
                    "billing_name": payment_method["billing_name"],
                    "billing_country": payment_method["billing_country"],
                    "is_default": bool(payment_method["is_default"]),
                    "status": str(payment_method["status"]),
                    "last_synced_at": payment_method["last_synced_at"],
                },
            )

        for product_access_state in payload["product_access_states"]:
            self._repository.upsert_product_access_state(
                account_id,
                product_code=str(product_access_state["product_code"]),
                state_data={
                    "access_state": str(product_access_state["access_state"]),
                    "launch_url": product_access_state["launch_url"],
                    "disabled_reason": product_access_state["disabled_reason"],
                    "external_account_reference": product_access_state["external_account_reference"],
                },
            )

    def _build_snapshot(
        self,
        account_id: UUID,
        *,
        pay_status: str,
        refreshed_from_pay: bool,
    ) -> PayProjectionSnapshot:
        return PayProjectionSnapshot(
            account_id=account_id,
            sync=PayProjectionSyncMetadata(
                pay_status=pay_status,
                refreshed_from_pay=refreshed_from_pay,
            ),
            subscriptions=[
                self._to_subscription_summary(summary)
                for summary in self._repository.list_subscription_summaries_for_account(account_id)
            ],
            entitlements=[
                self._to_entitlement_summary(summary)
                for summary in self._repository.list_entitlement_summaries_for_account(account_id)
            ],
            payments=[
                self._to_payment_summary(summary)
                for summary in self._repository.list_payment_summaries_for_account(account_id)
            ],
            payment_methods=[
                self._to_payment_method_summary(summary)
                for summary in self._repository.list_payment_method_summaries_for_account(account_id)
            ],
            product_access_states=[
                self._to_product_access_state(summary)
                for summary in self._repository.list_product_access_states_for_account(account_id)
            ],
        )

    @staticmethod
    def _normalize_projection_payload(payload: Any) -> Mapping[str, list[Mapping[str, Any]]]:
        if not isinstance(payload, Mapping):
            raise PayClientInvalidResponseError("Pay projection payload must be an object.")

        normalized_sections: dict[str, list[Mapping[str, Any]]] = {}
        for section_name in (
            "subscriptions",
            "entitlements",
            "payments",
            "payment_methods",
            "product_access_states",
        ):
            section = payload.get(section_name, [])
            if not isinstance(section, list):
                raise PayClientInvalidResponseError(
                    f"Pay projection section '{section_name}' must be a list."
                )
            normalized_sections[section_name] = [
                PayProjectionService._normalize_section_item(section_name, item) for item in section
            ]

        return normalized_sections

    @staticmethod
    def _normalize_section_item(
        section_name: str,
        item: Any,
    ) -> Mapping[str, Any]:
        if not isinstance(item, Mapping):
            raise PayClientInvalidResponseError(
                f"Pay projection section '{section_name}' contains an invalid item."
            )
        return item

    @staticmethod
    def _to_subscription_summary(
        summary: SubscriptionSummaryRecord,
    ) -> PayProjectionSubscriptionSummary:
        return PayProjectionSubscriptionSummary(
            product_code=summary.product_code,
            plan_code=summary.plan_code,
            billing_interval=summary.billing_interval,
            normalized_status=summary.normalized_status,
            provider_status_raw=summary.provider_status_raw,
            current_period_start_at=summary.current_period_start_at,
            current_period_end_at=summary.current_period_end_at,
            cancel_at_period_end=summary.cancel_at_period_end,
            canceled_at=summary.canceled_at,
            next_billing_at=summary.next_billing_at,
            last_synced_at=summary.last_synced_at,
        )

    @staticmethod
    def _to_entitlement_summary(
        summary: EntitlementSummaryRecord,
    ) -> PayProjectionEntitlementSummary:
        return PayProjectionEntitlementSummary(
            product_code=summary.product_code,
            plan_code=summary.plan_code,
            status=summary.status,
            starts_at=summary.starts_at,
            ends_at=summary.ends_at,
            last_synced_at=summary.last_synced_at,
        )

    @staticmethod
    def _to_payment_summary(summary: PaymentSummaryRecord) -> PayProjectionPaymentSummary:
        return PayProjectionPaymentSummary(
            product_code=summary.product_code,
            payment_rail=summary.payment_rail,
            normalized_status=summary.normalized_status,
            amount_cents=summary.amount_cents,
            currency=summary.currency,
            paid_at=summary.paid_at,
            updated_at=summary.updated_at,
        )

    @staticmethod
    def _to_payment_method_summary(
        summary: PaymentMethodSummaryRecord,
    ) -> PayProjectionPaymentMethodSummary:
        return PayProjectionPaymentMethodSummary(
            provider=summary.provider,
            brand=summary.brand,
            last4=summary.last4,
            exp_month=summary.exp_month,
            exp_year=summary.exp_year,
            billing_name=summary.billing_name,
            billing_country=summary.billing_country,
            is_default=summary.is_default,
            status=summary.status,
            last_synced_at=summary.last_synced_at,
        )

    @staticmethod
    def _to_product_access_state(
        summary: ProductAccessStateRecord,
    ) -> PayProjectionProductAccessState:
        return PayProjectionProductAccessState(
            product_code=summary.product_code,
            access_state=summary.access_state,
            launch_url=summary.launch_url,
            disabled_reason=summary.disabled_reason,
            updated_at=summary.updated_at,
        )


def build_pay_projection_service(db: Session, pay_client: PayClient) -> PayProjectionService:
    return PayProjectionService(PayProjectionRepository(db), pay_client)
