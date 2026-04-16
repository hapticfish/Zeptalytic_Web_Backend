from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.models.accounts import Account
from app.db.models.addresses import Address
from app.db.models.discord_connection_history import DiscordConnectionHistory
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_events import RewardEvent
from app.db.models.support_ticket_attachments import SupportTicketAttachment
from app.db.models.support_tickets import SupportTicket
from app.db.session import SessionLocal, engine


def _unique_suffix() -> str:
    return uuid4().hex[:12]


def _build_account(suffix: str) -> Account:
    return Account(
        username=f"user_{suffix}",
        email=f"user_{suffix}@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )


def _cleanup_accounts(account_ids: list[UUID]) -> None:
    with SessionLocal() as session:
        for account_id in account_ids:
            account = session.get(Account, account_id)
            if account is not None:
                session.delete(account)
        session.commit()


def test_parent_db_rejects_duplicate_usernames() -> None:
    account_ids: list[UUID] = []
    suffix = _unique_suffix()

    try:
        with SessionLocal() as session:
            account = _build_account(f"{suffix}_a")
            session.add(account)
            session.commit()
            account_ids.append(account.id)

            duplicate_username = Account(
                username=account.username,
                email=f"user_{suffix}_b@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(duplicate_username)

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()
    finally:
        _cleanup_accounts(account_ids)


def test_parent_db_discord_history_requires_existing_account() -> None:
    with SessionLocal() as session:
        session.add(
            DiscordConnectionHistory(
                account_id=uuid4(),
                discord_user_id="discord-missing-account",
                discord_username="missing_user",
                status="connected",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()


def test_parent_db_rejects_duplicate_support_codes_and_attachment_storage_keys() -> None:
    account_ids: list[UUID] = []
    suffix = _unique_suffix()
    ticket_code = f"SUP-{suffix}"
    storage_key = f"support/{suffix}/artifact.txt"

    try:
        with SessionLocal() as session:
            first_account = _build_account(f"{suffix}_a")
            second_account = _build_account(f"{suffix}_b")
            session.add_all([first_account, second_account])
            session.commit()
            account_ids.extend([first_account.id, second_account.id])

            first_ticket = SupportTicket(
                ticket_code=ticket_code,
                account_id=first_account.id,
                request_type="billing",
                related_product_code="parent-web",
                priority="high",
                subject="Constraint regression ticket",
                description="Verifies support ticket uniqueness in Postgres.",
                status="open",
                estimated_response_sla_label="24h",
            )
            session.add(first_ticket)
            session.commit()

            duplicate_ticket = SupportTicket(
                ticket_code=ticket_code,
                account_id=second_account.id,
                request_type="billing",
                related_product_code="parent-web",
                priority="high",
                subject="Duplicate ticket code",
                description="Should fail because ticket_code is unique.",
                status="open",
                estimated_response_sla_label="24h",
            )
            session.add(duplicate_ticket)

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

            second_ticket = SupportTicket(
                ticket_code=f"SUP-{suffix}-2",
                account_id=second_account.id,
                request_type="billing",
                related_product_code="parent-web",
                priority="high",
                subject="Attachment uniqueness setup",
                description="Creates a second ticket for attachment uniqueness coverage.",
                status="open",
                estimated_response_sla_label="24h",
            )
            session.add(second_ticket)
            session.commit()

            first_attachment = SupportTicketAttachment(
                ticket_id=first_ticket.id,
                uploaded_by_account_id=first_account.id,
                storage_key=storage_key,
                original_filename="artifact.txt",
                content_type="text/plain",
                file_size_bytes=128,
                scan_status="clean",
            )
            session.add(first_attachment)
            session.commit()

            duplicate_attachment = SupportTicketAttachment(
                ticket_id=second_ticket.id,
                uploaded_by_account_id=second_account.id,
                storage_key=storage_key,
                original_filename="artifact-copy.txt",
                content_type="text/plain",
                file_size_bytes=256,
                scan_status="clean",
            )
            session.add(duplicate_attachment)

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()
    finally:
        _cleanup_accounts(account_ids)


def test_parent_db_allows_multiple_primary_addresses_per_account() -> None:
    account_ids: list[UUID] = []
    suffix = _unique_suffix()

    try:
        with SessionLocal() as session:
            account = _build_account(suffix)
            session.add(account)
            session.commit()
            account_ids.append(account.id)

            first_address = Address(
                account_id=account.id,
                address_type="billing",
                label="Primary Billing",
                full_name="Primary Address User",
                line1="100 Main St",
                city_or_locality="Austin",
                state_or_region="TX",
                postal_code="78701",
                country_code="US",
                country_name="United States",
                formatted_address="100 Main St, Austin, TX 78701, US",
                is_primary=True,
            )
            second_address = Address(
                account_id=account.id,
                address_type="shipping",
                label="Primary Shipping",
                full_name="Primary Address User",
                line1="200 Main St",
                city_or_locality="Austin",
                state_or_region="TX",
                postal_code="78702",
                country_code="US",
                country_name="United States",
                formatted_address="200 Main St, Austin, TX 78702, US",
                is_primary=True,
            )
            session.add_all([first_address, second_address])
            session.commit()

            persisted_addresses = session.scalars(
                select(Address).where(Address.account_id == account.id)
            ).all()

            assert len(persisted_addresses) == 2
            assert all(address.is_primary is True for address in persisted_addresses)
    finally:
        _cleanup_accounts(account_ids)


def test_parent_db_projection_uniqueness_and_indexes_match_expected_contract() -> None:
    account_ids: list[UUID] = []
    suffix = _unique_suffix()
    synced_at = datetime(2026, 4, 14, tzinfo=timezone.utc)

    try:
        with SessionLocal() as session:
            first_account = _build_account(f"{suffix}_a")
            second_account = _build_account(f"{suffix}_b")
            session.add_all([first_account, second_account])
            session.commit()
            account_ids.extend([first_account.id, second_account.id])

            first_payment_method = PaymentMethodSummary(
                account_id=first_account.id,
                provider="stripe",
                provider_customer_id=f"cus_{suffix}_a",
                provider_payment_method_id=f"pm_{suffix}",
                brand="visa",
                last4="4242",
                exp_month=12,
                exp_year=2030,
                billing_name="Projection User A",
                billing_country="US",
                is_default=True,
                status="active",
                last_synced_at=synced_at,
            )
            session.add(first_payment_method)
            session.commit()

            duplicate_provider_method = PaymentMethodSummary(
                account_id=second_account.id,
                provider="stripe",
                provider_customer_id=f"cus_{suffix}_b",
                provider_payment_method_id=f"pm_{suffix}",
                brand="visa",
                last4="1111",
                exp_month=1,
                exp_year=2031,
                billing_name="Projection User B",
                billing_country="US",
                is_default=False,
                status="active",
                last_synced_at=synced_at,
            )
            session.add(duplicate_provider_method)

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

        inspector = inspect(engine)
        payment_method_indexes = {
            index["name"] for index in inspector.get_indexes("payment_method_summaries")
        }
        payment_summary_indexes = {
            index["name"] for index in inspector.get_indexes("payment_summaries")
        }
        subscription_indexes = {
            index["name"] for index in inspector.get_indexes("subscription_summaries")
        }
        support_ticket_indexes = {
            index["name"] for index in inspector.get_indexes("support_tickets")
        }

        assert "ix_payment_method_summaries_account_id" in payment_method_indexes
        assert "uq_payment_method_summaries_provider_method" in payment_method_indexes
        assert "ix_payment_summaries_account_id" in payment_summary_indexes
        assert "ix_payment_summaries_product_code" in payment_summary_indexes
        assert "ix_payment_summaries_payment_rail" in payment_summary_indexes
        assert "ix_subscription_summaries_account_id" in subscription_indexes
        assert "ix_subscription_summaries_product_code" in subscription_indexes
        assert "ix_support_tickets_account_id" in support_ticket_indexes
        assert "ix_support_tickets_status" in support_ticket_indexes
    finally:
        _cleanup_accounts(account_ids)


def test_parent_db_reward_event_requires_existing_account_and_indexes_exist() -> None:
    with SessionLocal() as session:
        session.add(
            RewardEvent(
                account_id=uuid4(),
                event_type="objective_completed",
                points_delta=100,
                source_type="objective",
                source_reference="objective:welcome",
                status="applied",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    inspector = inspect(engine)
    reward_event_indexes = {index["name"] for index in inspector.get_indexes("reward_events")}

    assert "ix_reward_events_account_id" in reward_event_indexes
    assert "ix_reward_events_created_at" in reward_event_indexes
    assert "ix_reward_events_reversed_event_id" in reward_event_indexes
