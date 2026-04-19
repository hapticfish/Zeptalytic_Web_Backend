from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.entitlement_summaries import EntitlementSummary
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.product_access_states import ProductAccessState
from app.db.models.subscription_summaries import SubscriptionSummary
from app.db.repositories.pay_projection_repository import PayProjectionRepository


def _create_in_memory_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    metadata = MetaData()
    for table in (
        Account.__table__,
        SubscriptionSummary.__table__,
        EntitlementSummary.__table__,
        PaymentSummary.__table__,
        PaymentMethodSummary.__table__,
        ProductAccessState.__table__,
    ):
        copied_table = table.to_metadata(metadata)
        for column in copied_table.c:
            if column.name == "metadata":
                column.server_default = None

    metadata.create_all(engine)
    return Session(engine)


def _create_account(session: Session, suffix: str = "pay_projection") -> Account:
    account = Account(
        username=f"{suffix}_{uuid4().hex[:8]}",
        email=f"{suffix}_{uuid4().hex[:8]}@example.com",
        password_hash="hashed-password",
        status="active",
        role="user",
    )
    session.add(account)
    session.commit()
    return account


def test_pay_projection_repository_lists_empty_collections_for_new_account() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "empty")
    repository = PayProjectionRepository(session)

    assert repository.list_subscription_summaries_for_account(account.id) == []
    assert repository.list_entitlement_summaries_for_account(account.id) == []
    assert repository.list_payment_summaries_for_account(account.id) == []
    assert repository.list_payment_method_summaries_for_account(account.id) == []
    assert repository.list_product_access_states_for_account(account.id) == []


def test_pay_projection_repository_upserts_current_projection_rows_by_account_and_product() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "current")
    repository = PayProjectionRepository(session)
    synced_at = datetime(2026, 4, 18, 22, 30, tzinfo=timezone.utc)
    updated_at = datetime(2026, 4, 18, 22, 35, tzinfo=timezone.utc)

    first_subscription = repository.upsert_subscription_summary(
        account.id,
        product_code="zardbot",
        summary_data={
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
        },
    )
    replaced_subscription = repository.upsert_subscription_summary(
        account.id,
        product_code="zardbot",
        summary_data={
            "plan_code": "starter-annual",
            "billing_interval": "year",
            "normalized_status": "past_due",
            "provider_status_raw": "past_due",
            "current_period_start_at": updated_at,
            "current_period_end_at": updated_at,
            "cancel_at_period_end": True,
            "canceled_at": updated_at,
            "next_billing_at": updated_at,
            "last_synced_at": updated_at,
        },
    )

    first_entitlement = repository.upsert_entitlement_summary(
        account.id,
        product_code="zardbot",
        summary_data={
            "plan_code": "starter-monthly",
            "status": "active",
            "starts_at": synced_at,
            "ends_at": None,
            "entitlement_metadata": {"source": "initial"},
            "last_synced_at": synced_at,
        },
    )
    replaced_entitlement = repository.upsert_entitlement_summary(
        account.id,
        product_code="zardbot",
        summary_data={
            "plan_code": "starter-annual",
            "status": "grace_period",
            "starts_at": synced_at,
            "ends_at": updated_at,
            "entitlement_metadata": {"source": "refresh"},
            "last_synced_at": updated_at,
        },
    )

    first_access_state = repository.upsert_product_access_state(
        account.id,
        product_code="zardbot",
        state_data={
            "access_state": "provision_pending",
            "launch_url": None,
            "disabled_reason": "Provisioning in progress",
            "external_account_reference": None,
        },
    )
    replaced_access_state = repository.upsert_product_access_state(
        account.id,
        product_code="zardbot",
        state_data={
            "access_state": "active",
            "launch_url": "https://launcher.example.com/zardbot",
            "disabled_reason": None,
            "external_account_reference": "acct_zardbot_001",
        },
    )

    subscription_rows = session.scalars(
        select(SubscriptionSummary).where(SubscriptionSummary.account_id == account.id)
    ).all()
    entitlement_rows = session.scalars(
        select(EntitlementSummary).where(EntitlementSummary.account_id == account.id)
    ).all()
    access_rows = session.scalars(
        select(ProductAccessState).where(ProductAccessState.account_id == account.id)
    ).all()

    assert first_subscription.summary_id == replaced_subscription.summary_id
    assert first_entitlement.summary_id == replaced_entitlement.summary_id
    assert first_access_state.state_id == replaced_access_state.state_id
    assert len(subscription_rows) == 1
    assert len(entitlement_rows) == 1
    assert len(access_rows) == 1
    assert repository.list_subscription_summaries_for_account(account.id)[0].plan_code == "starter-annual"
    assert repository.list_entitlement_summaries_for_account(account.id)[0].status == "grace_period"
    assert repository.list_product_access_states_for_account(account.id)[0].access_state == "active"


def test_pay_projection_repository_upserts_payment_summaries_by_provider_reference() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "payments")
    repository = PayProjectionRepository(session)
    paid_at = datetime(2026, 4, 18, 22, 40, tzinfo=timezone.utc)

    first_payment = repository.upsert_payment_summary(
        account.id,
        summary_data={
            "product_code": "zardbot",
            "payment_rail": "card",
            "normalized_status": "pending",
            "provider_status_raw": "requires_capture",
            "amount_cents": 4900,
            "currency": "USD",
            "paid_at": paid_at,
            "provider_payment_reference": "pi_123",
        },
    )
    replaced_payment = repository.upsert_payment_summary(
        account.id,
        summary_data={
            "product_code": "zardbot",
            "payment_rail": "card",
            "normalized_status": "succeeded",
            "provider_status_raw": "succeeded",
            "amount_cents": 4900,
            "currency": "USD",
            "paid_at": paid_at,
            "provider_payment_reference": "pi_123",
        },
    )
    second_payment = repository.upsert_payment_summary(
        account.id,
        summary_data={
            "product_code": "zardbot",
            "payment_rail": "card",
            "normalized_status": "succeeded",
            "provider_status_raw": "succeeded",
            "amount_cents": 9900,
            "currency": "USD",
            "paid_at": datetime(2026, 4, 18, 22, 45, tzinfo=timezone.utc),
            "provider_payment_reference": "pi_456",
        },
    )

    payment_rows = session.scalars(
        select(PaymentSummary).where(PaymentSummary.account_id == account.id)
    ).all()
    payment_records = repository.list_payment_summaries_for_account(account.id)

    assert first_payment.summary_id == replaced_payment.summary_id
    assert len(payment_rows) == 2
    assert second_payment.summary_id == payment_records[0].summary_id
    assert payment_records[1].normalized_status == "succeeded"


def test_pay_projection_repository_upserts_payment_methods_and_resets_prior_defaults() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "methods")
    repository = PayProjectionRepository(session)
    synced_at = datetime(2026, 4, 18, 22, 50, tzinfo=timezone.utc)

    first_method = repository.upsert_payment_method_summary(
        account.id,
        provider="stripe",
        provider_payment_method_id="pm_123",
        summary_data={
            "provider_customer_id": "cus_123",
            "brand": "visa",
            "last4": "4242",
            "exp_month": 12,
            "exp_year": 2030,
            "billing_name": "Projection User",
            "billing_country": "US",
            "is_default": True,
            "status": "active",
            "last_synced_at": synced_at,
        },
    )
    second_method = repository.upsert_payment_method_summary(
        account.id,
        provider="stripe",
        provider_payment_method_id="pm_456",
        summary_data={
            "provider_customer_id": "cus_123",
            "brand": "mastercard",
            "last4": "4444",
            "exp_month": 1,
            "exp_year": 2032,
            "billing_name": "Projection User",
            "billing_country": "US",
            "is_default": True,
            "status": "active",
            "last_synced_at": synced_at,
        },
    )
    replaced_first_method = repository.upsert_payment_method_summary(
        account.id,
        provider="stripe",
        provider_payment_method_id="pm_123",
        summary_data={
            "provider_customer_id": "cus_123",
            "brand": "visa",
            "last4": "1111",
            "exp_month": 6,
            "exp_year": 2034,
            "billing_name": "Projection User Updated",
            "billing_country": "CA",
            "is_default": False,
            "status": "inactive",
            "last_synced_at": synced_at,
        },
    )

    payment_method_records = repository.list_payment_method_summaries_for_account(account.id)
    persisted_methods = session.scalars(
        select(PaymentMethodSummary)
        .where(PaymentMethodSummary.account_id == account.id)
        .order_by(PaymentMethodSummary.provider_payment_method_id.asc())
    ).all()

    assert first_method.summary_id == replaced_first_method.summary_id
    assert len(persisted_methods) == 2
    assert persisted_methods[0].is_default is False
    assert persisted_methods[0].last4 == "1111"
    assert persisted_methods[1].is_default is True
    assert payment_method_records[0].summary_id == second_method.summary_id
