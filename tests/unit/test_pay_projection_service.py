from __future__ import annotations

import ast
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from app.db.repositories.pay_projection_repository import (
    EntitlementSummaryRecord,
    PaymentMethodSummaryRecord,
    PaymentSummaryRecord,
    ProductAccessStateRecord,
    SubscriptionSummaryRecord,
)
from app.integrations import PayClientInvalidResponseError, PayClientUnavailableError
from app.services.pay_projection_service import (
    PayProjectionPaymentMethodSummary,
    PayProjectionPaymentSummary,
    PayProjectionService,
)


@dataclass
class StubPayClient:
    payload: object | None = None
    error: Exception | None = None

    def __post_init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def request_json(self, method: str, path: str):  # noqa: ANN001
        self.calls.append((method, path))
        if self.error is not None:
            raise self.error
        return self.payload


class StubPayProjectionRepository:
    def __init__(self) -> None:
        self.subscription_records: list[SubscriptionSummaryRecord] = []
        self.entitlement_records: list[EntitlementSummaryRecord] = []
        self.payment_records: list[PaymentSummaryRecord] = []
        self.payment_method_records: list[PaymentMethodSummaryRecord] = []
        self.product_access_records: list[ProductAccessStateRecord] = []
        self.subscription_upserts: list[dict[str, object]] = []
        self.entitlement_upserts: list[dict[str, object]] = []
        self.payment_upserts: list[dict[str, object]] = []
        self.payment_method_upserts: list[dict[str, object]] = []
        self.product_access_upserts: list[dict[str, object]] = []
        self.commits = 0
        self.rollbacks = 0

    def list_subscription_summaries_for_account(self, account_id: UUID) -> list[SubscriptionSummaryRecord]:
        del account_id
        return list(self.subscription_records)

    def list_entitlement_summaries_for_account(self, account_id: UUID) -> list[EntitlementSummaryRecord]:
        del account_id
        return list(self.entitlement_records)

    def list_payment_summaries_for_account(self, account_id: UUID) -> list[PaymentSummaryRecord]:
        del account_id
        return list(self.payment_records)

    def list_payment_method_summaries_for_account(
        self, account_id: UUID
    ) -> list[PaymentMethodSummaryRecord]:
        del account_id
        return list(self.payment_method_records)

    def list_product_access_states_for_account(
        self, account_id: UUID
    ) -> list[ProductAccessStateRecord]:
        del account_id
        return list(self.product_access_records)

    def upsert_subscription_summary(
        self,
        account_id: UUID,
        *,
        product_code: str,
        summary_data: dict[str, object],
    ) -> SubscriptionSummaryRecord:
        record = SubscriptionSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code=product_code,
            plan_code=str(summary_data["plan_code"]),
            billing_interval=str(summary_data["billing_interval"]),
            normalized_status=str(summary_data["normalized_status"]),
            provider_status_raw=str(summary_data["provider_status_raw"]),
            current_period_start_at=summary_data["current_period_start_at"],
            current_period_end_at=summary_data["current_period_end_at"],
            cancel_at_period_end=bool(summary_data["cancel_at_period_end"]),
            canceled_at=summary_data["canceled_at"],
            next_billing_at=summary_data["next_billing_at"],
            last_synced_at=summary_data["last_synced_at"],
        )
        self.subscription_upserts.append(
            {"account_id": account_id, "product_code": product_code, "summary_data": summary_data}
        )
        self.subscription_records = [record]
        return record

    def upsert_entitlement_summary(
        self,
        account_id: UUID,
        *,
        product_code: str,
        summary_data: dict[str, object],
    ) -> EntitlementSummaryRecord:
        record = EntitlementSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code=product_code,
            plan_code=str(summary_data["plan_code"]),
            status=str(summary_data["status"]),
            starts_at=summary_data["starts_at"],
            ends_at=summary_data["ends_at"],
            entitlement_metadata=dict(summary_data["entitlement_metadata"]),
            last_synced_at=summary_data["last_synced_at"],
        )
        self.entitlement_upserts.append(
            {"account_id": account_id, "product_code": product_code, "summary_data": summary_data}
        )
        self.entitlement_records = [record]
        return record

    def upsert_payment_summary(
        self,
        account_id: UUID,
        *,
        summary_data: dict[str, object],
    ) -> PaymentSummaryRecord:
        record = PaymentSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code=summary_data["product_code"],
            payment_rail=str(summary_data["payment_rail"]),
            normalized_status=str(summary_data["normalized_status"]),
            provider_status_raw=summary_data["provider_status_raw"],
            amount_cents=int(summary_data["amount_cents"]),
            currency=str(summary_data["currency"]),
            paid_at=summary_data["paid_at"],
            provider_payment_reference=summary_data["provider_payment_reference"],
            updated_at=datetime(2026, 4, 18, 23, 0, tzinfo=timezone.utc),
        )
        self.payment_upserts.append({"account_id": account_id, "summary_data": summary_data})
        self.payment_records = [record]
        return record

    def upsert_payment_method_summary(
        self,
        account_id: UUID,
        *,
        provider: str,
        provider_payment_method_id: str,
        summary_data: dict[str, object],
    ) -> PaymentMethodSummaryRecord:
        record = PaymentMethodSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            provider=provider,
            provider_customer_id=str(summary_data["provider_customer_id"]),
            provider_payment_method_id=provider_payment_method_id,
            brand=str(summary_data["brand"]),
            last4=str(summary_data["last4"]),
            exp_month=int(summary_data["exp_month"]),
            exp_year=int(summary_data["exp_year"]),
            billing_name=summary_data["billing_name"],
            billing_country=summary_data["billing_country"],
            is_default=bool(summary_data["is_default"]),
            status=str(summary_data["status"]),
            last_synced_at=summary_data["last_synced_at"],
        )
        self.payment_method_upserts.append(
            {
                "account_id": account_id,
                "provider": provider,
                "provider_payment_method_id": provider_payment_method_id,
                "summary_data": summary_data,
            }
        )
        self.payment_method_records = [record]
        return record

    def upsert_product_access_state(
        self,
        account_id: UUID,
        *,
        product_code: str,
        state_data: dict[str, object],
    ) -> ProductAccessStateRecord:
        record = ProductAccessStateRecord(
            state_id=uuid4(),
            account_id=account_id,
            product_code=product_code,
            access_state=str(state_data["access_state"]),
            launch_url=state_data["launch_url"],
            disabled_reason=state_data["disabled_reason"],
            external_account_reference=state_data["external_account_reference"],
            updated_at=datetime(2026, 4, 18, 23, 5, tzinfo=timezone.utc),
        )
        self.product_access_upserts.append(
            {"account_id": account_id, "product_code": product_code, "state_data": state_data}
        )
        self.product_access_records = [record]
        return record

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_pay_projection_service_refreshes_and_returns_normalized_snapshot() -> None:
    account_id = uuid4()
    synced_at = datetime(2026, 4, 18, 22, 58, tzinfo=timezone.utc)
    repository = StubPayProjectionRepository()
    client = StubPayClient(
        payload={
            "subscriptions": [
                {
                    "product_code": "zardbot",
                    "plan_code": "starter-monthly",
                    "billing_interval": "month",
                    "normalized_status": "active",
                    "provider_status_raw": "active",
                    "current_period_start_at": synced_at,
                    "current_period_end_at": synced_at,
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "next_billing_at": synced_at,
                    "last_synced_at": synced_at,
                }
            ],
            "entitlements": [
                {
                    "product_code": "zardbot",
                    "plan_code": "starter-monthly",
                    "status": "active",
                    "starts_at": synced_at,
                    "ends_at": None,
                    "entitlement_metadata": {"source": "pay"},
                    "last_synced_at": synced_at,
                }
            ],
            "payments": [
                {
                    "product_code": "zardbot",
                    "payment_rail": "card",
                    "normalized_status": "succeeded",
                    "provider_status_raw": "succeeded",
                    "amount_cents": 4900,
                    "currency": "USD",
                    "paid_at": synced_at,
                    "provider_payment_reference": "pi_123",
                }
            ],
            "payment_methods": [
                {
                    "provider": "stripe",
                    "provider_customer_id": "cus_123",
                    "provider_payment_method_id": "pm_123",
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 12,
                    "exp_year": 2030,
                    "billing_name": "Projection User",
                    "billing_country": "US",
                    "is_default": True,
                    "status": "active",
                    "last_synced_at": synced_at,
                }
            ],
            "product_access_states": [
                {
                    "product_code": "zardbot",
                    "access_state": "active",
                    "launch_url": "https://launcher.example.com/zardbot",
                    "disabled_reason": None,
                    "external_account_reference": "acct_zardbot_123",
                }
            ],
        }
    )
    service = PayProjectionService(repository, client)

    snapshot = service.refresh_account_snapshot(account_id)

    assert client.calls == [("GET", f"/internal/accounts/{account_id}/projection-summary")]
    assert repository.commits == 1
    assert repository.rollbacks == 0
    assert len(repository.subscription_upserts) == 1
    assert len(repository.entitlement_upserts) == 1
    assert len(repository.payment_upserts) == 1
    assert len(repository.payment_method_upserts) == 1
    assert len(repository.product_access_upserts) == 1
    assert snapshot.sync.pay_status == "available"
    assert snapshot.sync.refreshed_from_pay is True
    assert snapshot.subscriptions[0].plan_code == "starter-monthly"
    assert snapshot.entitlements[0].status == "active"
    assert snapshot.payments[0].normalized_status == "succeeded"
    assert snapshot.payment_methods[0].last4 == "4242"
    assert snapshot.product_access_states[0].access_state == "active"


def test_pay_projection_service_snapshot_uses_safe_service_owned_types() -> None:
    account_id = uuid4()
    repository = StubPayProjectionRepository()
    repository.payment_records = [
        PaymentSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code="zardbot",
            payment_rail="card",
            normalized_status="succeeded",
            provider_status_raw="succeeded",
            amount_cents=4900,
            currency="USD",
            paid_at=datetime(2026, 4, 18, 19, 0, tzinfo=timezone.utc),
            provider_payment_reference="pi_hidden",
            updated_at=datetime(2026, 4, 18, 19, 5, tzinfo=timezone.utc),
        )
    ]
    repository.payment_method_records = [
        PaymentMethodSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            provider="stripe",
            provider_customer_id="cus_hidden",
            provider_payment_method_id="pm_hidden",
            brand="visa",
            last4="4242",
            exp_month=12,
            exp_year=2030,
            billing_name="Projection User",
            billing_country="US",
            is_default=True,
            status="active",
            last_synced_at=datetime(2026, 4, 18, 19, 10, tzinfo=timezone.utc),
        )
    ]
    repository.product_access_records = [
        ProductAccessStateRecord(
            state_id=uuid4(),
            account_id=account_id,
            product_code="zardbot",
            access_state="active",
            launch_url="https://launcher.example.com/zardbot",
            disabled_reason=None,
            external_account_reference="acct_hidden",
            updated_at=datetime(2026, 4, 18, 19, 15, tzinfo=timezone.utc),
        )
    ]
    service = PayProjectionService(repository, StubPayClient(payload={}))

    snapshot = service.get_cached_snapshot(account_id)

    assert isinstance(snapshot.payments[0], PayProjectionPaymentSummary)
    assert isinstance(snapshot.payment_methods[0], PayProjectionPaymentMethodSummary)
    assert "provider_payment_reference" not in asdict(snapshot.payments[0])
    assert "provider_customer_id" not in asdict(snapshot.payment_methods[0])
    assert "provider_payment_method_id" not in asdict(snapshot.payment_methods[0])
    assert "external_account_reference" not in asdict(snapshot.product_access_states[0])


def test_pay_projection_service_returns_cached_snapshot_when_pay_is_unavailable() -> None:
    account_id = uuid4()
    repository = StubPayProjectionRepository()
    repository.subscription_records = [
        SubscriptionSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code="zardbot",
            plan_code="starter-annual",
            billing_interval="year",
            normalized_status="past_due",
            provider_status_raw="past_due",
            current_period_start_at=None,
            current_period_end_at=None,
            cancel_at_period_end=True,
            canceled_at=None,
            next_billing_at=None,
            last_synced_at=datetime(2026, 4, 18, 21, 0, tzinfo=timezone.utc),
        )
    ]
    client = StubPayClient(
        error=PayClientUnavailableError("Pay service is unavailable."),
    )
    service = PayProjectionService(repository, client)

    snapshot = service.refresh_account_snapshot(account_id)

    assert repository.commits == 0
    assert repository.rollbacks == 1
    assert snapshot.sync.pay_status == "unavailable"
    assert snapshot.sync.refreshed_from_pay is False
    assert snapshot.subscriptions[0].normalized_status == "past_due"


def test_pay_projection_service_treats_invalid_payload_as_safe_fallback() -> None:
    account_id = uuid4()
    repository = StubPayProjectionRepository()
    repository.payment_method_records = [
        PaymentMethodSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            provider="stripe",
            provider_customer_id="cus_cached",
            provider_payment_method_id="pm_cached",
            brand="visa",
            last4="1111",
            exp_month=1,
            exp_year=2031,
            billing_name="Cached User",
            billing_country="US",
            is_default=True,
            status="active",
            last_synced_at=datetime(2026, 4, 18, 20, 0, tzinfo=timezone.utc),
        )
    ]
    client = StubPayClient(payload={"subscriptions": "invalid"})
    service = PayProjectionService(repository, client)

    snapshot = service.refresh_account_snapshot(account_id)

    assert repository.commits == 0
    assert repository.rollbacks == 1
    assert snapshot.sync.pay_status == "unavailable"
    assert snapshot.payment_methods[0].last4 == "1111"


def test_pay_projection_service_get_cached_snapshot_marks_projection_only_status() -> None:
    account_id = uuid4()
    repository = StubPayProjectionRepository()
    repository.payment_records = [
        PaymentSummaryRecord(
            summary_id=uuid4(),
            account_id=account_id,
            product_code="zardbot",
            payment_rail="card",
            normalized_status="succeeded",
            provider_status_raw="succeeded",
            amount_cents=4900,
            currency="USD",
            paid_at=datetime(2026, 4, 18, 19, 0, tzinfo=timezone.utc),
            provider_payment_reference="pi_cached",
            updated_at=datetime(2026, 4, 18, 19, 5, tzinfo=timezone.utc),
        )
    ]
    client = StubPayClient(
        error=PayClientInvalidResponseError("unused"),
    )
    service = PayProjectionService(repository, client)

    snapshot = service.get_cached_snapshot(account_id)

    assert client.calls == []
    assert repository.commits == 0
    assert repository.rollbacks == 0
    assert snapshot.sync.pay_status == "projection_only"
    assert snapshot.sync.refreshed_from_pay is False
    assert snapshot.payments[0].payment_rail == "card"


def test_pay_projection_service_public_api_stays_projection_read_only() -> None:
    module_path = Path("app/services/pay_projection_service.py")
    parsed = ast.parse(module_path.read_text(encoding="utf-8"))
    service_class = next(
        node for node in parsed.body if isinstance(node, ast.ClassDef) and node.name == "PayProjectionService"
    )

    public_methods = [
        node.name for node in service_class.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]

    assert public_methods == ["get_cached_snapshot", "refresh_account_snapshot"]
