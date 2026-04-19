from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db.models.entitlement_summaries import EntitlementSummary
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.product_access_states import ProductAccessState
from app.db.models.subscription_summaries import SubscriptionSummary


@dataclass(slots=True)
class SubscriptionSummaryRecord:
    summary_id: UUID
    account_id: UUID
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
class EntitlementSummaryRecord:
    summary_id: UUID
    account_id: UUID
    product_code: str
    plan_code: str
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    entitlement_metadata: dict[str, object]
    last_synced_at: datetime


@dataclass(slots=True)
class PaymentSummaryRecord:
    summary_id: UUID
    account_id: UUID
    product_code: str | None
    payment_rail: str
    normalized_status: str
    provider_status_raw: str | None
    amount_cents: int
    currency: str
    paid_at: datetime | None
    provider_payment_reference: str | None
    updated_at: datetime


@dataclass(slots=True)
class PaymentMethodSummaryRecord:
    summary_id: UUID
    account_id: UUID
    provider: str
    provider_customer_id: str
    provider_payment_method_id: str
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
class ProductAccessStateRecord:
    state_id: UUID
    account_id: UUID
    product_code: str
    access_state: str
    launch_url: str | None
    disabled_reason: str | None
    external_account_reference: str | None
    updated_at: datetime


class PayProjectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def list_subscription_summaries_for_account(
        self, account_id: UUID
    ) -> list[SubscriptionSummaryRecord]:
        rows = self._db.scalars(
            select(SubscriptionSummary)
            .where(SubscriptionSummary.account_id == account_id)
            .order_by(SubscriptionSummary.product_code.asc(), SubscriptionSummary.id.asc())
        ).all()
        return [self._to_subscription_record(row) for row in rows]

    def upsert_subscription_summary(
        self,
        account_id: UUID,
        *,
        product_code: str,
        summary_data: dict[str, object],
    ) -> SubscriptionSummaryRecord:
        summary = self._get_current_subscription_summary(account_id, product_code)
        if summary is None:
            summary = SubscriptionSummary(account_id=account_id, product_code=product_code, **summary_data)
            self._db.add(summary)
            self._db.flush()
            return self._to_subscription_record(summary)

        self._apply_updates(summary, summary_data)
        self._db.flush()
        self._delete_duplicate_subscription_summaries(account_id, product_code, keep_id=summary.id)
        self._db.flush()
        return self._to_subscription_record(summary)

    def list_entitlement_summaries_for_account(
        self, account_id: UUID
    ) -> list[EntitlementSummaryRecord]:
        rows = self._db.scalars(
            select(EntitlementSummary)
            .where(EntitlementSummary.account_id == account_id)
            .order_by(EntitlementSummary.product_code.asc(), EntitlementSummary.id.asc())
        ).all()
        return [self._to_entitlement_record(row) for row in rows]

    def upsert_entitlement_summary(
        self,
        account_id: UUID,
        *,
        product_code: str,
        summary_data: dict[str, object],
    ) -> EntitlementSummaryRecord:
        summary = self._get_current_entitlement_summary(account_id, product_code)
        if summary is None:
            summary = EntitlementSummary(account_id=account_id, product_code=product_code, **summary_data)
            self._db.add(summary)
            self._db.flush()
            return self._to_entitlement_record(summary)

        self._apply_updates(summary, summary_data)
        self._db.flush()
        self._delete_duplicate_entitlement_summaries(account_id, product_code, keep_id=summary.id)
        self._db.flush()
        return self._to_entitlement_record(summary)

    def list_payment_summaries_for_account(self, account_id: UUID) -> list[PaymentSummaryRecord]:
        rows = self._db.scalars(
            select(PaymentSummary)
            .where(PaymentSummary.account_id == account_id)
            .order_by(
                PaymentSummary.paid_at.desc().nullslast(),
                PaymentSummary.updated_at.desc(),
                PaymentSummary.id.desc(),
            )
        ).all()
        return [self._to_payment_record(row) for row in rows]

    def upsert_payment_summary(
        self,
        account_id: UUID,
        *,
        summary_data: dict[str, object],
    ) -> PaymentSummaryRecord:
        summary = self._get_current_payment_summary(account_id, summary_data)
        if summary is None:
            summary = PaymentSummary(account_id=account_id, **summary_data)
            self._db.add(summary)
            self._db.flush()
            return self._to_payment_record(summary)

        self._apply_updates(summary, summary_data)
        self._db.flush()
        return self._to_payment_record(summary)

    def list_payment_method_summaries_for_account(
        self, account_id: UUID
    ) -> list[PaymentMethodSummaryRecord]:
        rows = self._db.scalars(
            select(PaymentMethodSummary)
            .where(PaymentMethodSummary.account_id == account_id)
            .order_by(
                PaymentMethodSummary.is_default.desc(),
                PaymentMethodSummary.last_synced_at.desc(),
                PaymentMethodSummary.id.desc(),
            )
        ).all()
        return [self._to_payment_method_record(row) for row in rows]

    def upsert_payment_method_summary(
        self,
        account_id: UUID,
        *,
        provider: str,
        provider_payment_method_id: str,
        summary_data: dict[str, object],
    ) -> PaymentMethodSummaryRecord:
        summary = self._db.scalar(
            select(PaymentMethodSummary).where(
                PaymentMethodSummary.provider == provider,
                PaymentMethodSummary.provider_payment_method_id == provider_payment_method_id,
            )
        )

        if summary is None:
            summary = PaymentMethodSummary(
                account_id=account_id,
                provider=provider,
                provider_payment_method_id=provider_payment_method_id,
                **summary_data,
            )
            self._db.add(summary)
        else:
            summary.account_id = account_id
            self._apply_updates(summary, summary_data)

        self._db.flush()

        if summary.is_default:
            self._db.execute(
                update(PaymentMethodSummary)
                .where(
                    PaymentMethodSummary.account_id == account_id,
                    PaymentMethodSummary.id != summary.id,
                )
                .values(is_default=False)
            )

        self._db.flush()
        return self._to_payment_method_record(summary)

    def list_product_access_states_for_account(
        self, account_id: UUID
    ) -> list[ProductAccessStateRecord]:
        rows = self._db.scalars(
            select(ProductAccessState)
            .where(ProductAccessState.account_id == account_id)
            .order_by(ProductAccessState.product_code.asc(), ProductAccessState.id.asc())
        ).all()
        return [self._to_product_access_record(row) for row in rows]

    def upsert_product_access_state(
        self,
        account_id: UUID,
        *,
        product_code: str,
        state_data: dict[str, object],
    ) -> ProductAccessStateRecord:
        state = self._get_current_product_access_state(account_id, product_code)
        if state is None:
            state = ProductAccessState(account_id=account_id, product_code=product_code, **state_data)
            self._db.add(state)
            self._db.flush()
            return self._to_product_access_record(state)

        self._apply_updates(state, state_data)
        self._db.flush()
        self._delete_duplicate_product_access_states(account_id, product_code, keep_id=state.id)
        self._db.flush()
        return self._to_product_access_record(state)

    def _get_current_subscription_summary(
        self, account_id: UUID, product_code: str
    ) -> SubscriptionSummary | None:
        return self._db.scalar(
            select(SubscriptionSummary)
            .where(
                SubscriptionSummary.account_id == account_id,
                SubscriptionSummary.product_code == product_code,
            )
            .order_by(SubscriptionSummary.last_synced_at.desc(), SubscriptionSummary.id.desc())
            .limit(1)
        )

    def _get_current_entitlement_summary(
        self, account_id: UUID, product_code: str
    ) -> EntitlementSummary | None:
        return self._db.scalar(
            select(EntitlementSummary)
            .where(
                EntitlementSummary.account_id == account_id,
                EntitlementSummary.product_code == product_code,
            )
            .order_by(EntitlementSummary.last_synced_at.desc(), EntitlementSummary.id.desc())
            .limit(1)
        )

    def _get_current_payment_summary(
        self,
        account_id: UUID,
        summary_data: dict[str, object],
    ) -> PaymentSummary | None:
        provider_payment_reference = summary_data.get("provider_payment_reference")
        if provider_payment_reference:
            return self._db.scalar(
                select(PaymentSummary).where(
                    PaymentSummary.account_id == account_id,
                    PaymentSummary.provider_payment_reference == provider_payment_reference,
                )
            )

        return self._db.scalar(
            select(PaymentSummary)
            .where(
                PaymentSummary.account_id == account_id,
                PaymentSummary.product_code == summary_data.get("product_code"),
                PaymentSummary.payment_rail == summary_data["payment_rail"],
            )
            .order_by(
                PaymentSummary.paid_at.desc().nullslast(),
                PaymentSummary.updated_at.desc(),
                PaymentSummary.id.desc(),
            )
            .limit(1)
        )

    def _get_current_product_access_state(
        self, account_id: UUID, product_code: str
    ) -> ProductAccessState | None:
        return self._db.scalar(
            select(ProductAccessState)
            .where(
                ProductAccessState.account_id == account_id,
                ProductAccessState.product_code == product_code,
            )
            .order_by(ProductAccessState.updated_at.desc(), ProductAccessState.id.desc())
            .limit(1)
        )

    def _delete_duplicate_subscription_summaries(
        self, account_id: UUID, product_code: str, *, keep_id: UUID
    ) -> None:
        self._db.execute(
            delete(SubscriptionSummary).where(
                SubscriptionSummary.account_id == account_id,
                SubscriptionSummary.product_code == product_code,
                SubscriptionSummary.id != keep_id,
            )
        )

    def _delete_duplicate_entitlement_summaries(
        self, account_id: UUID, product_code: str, *, keep_id: UUID
    ) -> None:
        self._db.execute(
            delete(EntitlementSummary).where(
                EntitlementSummary.account_id == account_id,
                EntitlementSummary.product_code == product_code,
                EntitlementSummary.id != keep_id,
            )
        )

    def _delete_duplicate_product_access_states(
        self, account_id: UUID, product_code: str, *, keep_id: UUID
    ) -> None:
        self._db.execute(
            delete(ProductAccessState).where(
                ProductAccessState.account_id == account_id,
                ProductAccessState.product_code == product_code,
                ProductAccessState.id != keep_id,
            )
        )

    @staticmethod
    def _apply_updates(model: object, updates: dict[str, object]) -> None:
        for field_name, value in updates.items():
            setattr(model, field_name, value)

    @staticmethod
    def _to_subscription_record(summary: SubscriptionSummary) -> SubscriptionSummaryRecord:
        return SubscriptionSummaryRecord(
            summary_id=summary.id,
            account_id=summary.account_id,
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
    def _to_entitlement_record(summary: EntitlementSummary) -> EntitlementSummaryRecord:
        return EntitlementSummaryRecord(
            summary_id=summary.id,
            account_id=summary.account_id,
            product_code=summary.product_code,
            plan_code=summary.plan_code,
            status=summary.status,
            starts_at=summary.starts_at,
            ends_at=summary.ends_at,
            entitlement_metadata=dict(summary.entitlement_metadata),
            last_synced_at=summary.last_synced_at,
        )

    @staticmethod
    def _to_payment_record(summary: PaymentSummary) -> PaymentSummaryRecord:
        return PaymentSummaryRecord(
            summary_id=summary.id,
            account_id=summary.account_id,
            product_code=summary.product_code,
            payment_rail=summary.payment_rail,
            normalized_status=summary.normalized_status,
            provider_status_raw=summary.provider_status_raw,
            amount_cents=summary.amount_cents,
            currency=summary.currency,
            paid_at=summary.paid_at,
            provider_payment_reference=summary.provider_payment_reference,
            updated_at=summary.updated_at,
        )

    @staticmethod
    def _to_payment_method_record(
        summary: PaymentMethodSummary,
    ) -> PaymentMethodSummaryRecord:
        return PaymentMethodSummaryRecord(
            summary_id=summary.id,
            account_id=summary.account_id,
            provider=summary.provider,
            provider_customer_id=summary.provider_customer_id,
            provider_payment_method_id=summary.provider_payment_method_id,
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
    def _to_product_access_record(state: ProductAccessState) -> ProductAccessStateRecord:
        return ProductAccessStateRecord(
            state_id=state.id,
            account_id=state.account_id,
            product_code=state.product_code,
            access_state=state.access_state,
            launch_url=state.launch_url,
            disabled_reason=state.disabled_reason,
            external_account_reference=state.external_account_reference,
            updated_at=state.updated_at,
        )
