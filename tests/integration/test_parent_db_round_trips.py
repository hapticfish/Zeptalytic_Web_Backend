from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.accounts import Account
from app.db.models.addresses import Address
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.profiles import Profile
from app.db.models.subscription_summaries import SubscriptionSummary
from app.db.models.support_ticket_attachments import SupportTicketAttachment
from app.db.models.support_ticket_messages import SupportTicketMessage
from app.db.models.support_tickets import SupportTicket
from app.db.session import SessionLocal


def _unique_suffix() -> str:
    return uuid4().hex[:12]


def _cleanup_account(account_id: UUID) -> None:
    with SessionLocal() as session:
        account = session.get(Account, account_id)
        if account is not None:
            session.delete(account)
            session.commit()


def test_parent_identity_address_and_support_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"roundtrip_{suffix}",
                email=f"roundtrip_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            address = Address(
                account_id=account.id,
                address_type="billing",
                label="Primary",
                full_name="Round Trip User",
                line1="100 Integration Way",
                city_or_locality="Austin",
                state_or_region="TX",
                postal_code="78701",
                country_code="US",
                country_name="United States",
                formatted_address="100 Integration Way, Austin, TX 78701, US",
                is_primary=True,
            )
            ticket = SupportTicket(
                ticket_code=f"TCK-{suffix}",
                account_id=account.id,
                request_type="billing",
                related_product_code="parent-web",
                priority="high",
                subject="Round-trip support verification",
                description="Verifies support persistence in migrated Postgres.",
                status="open",
                estimated_response_sla_label="24h",
            )
            session.add_all([address, ticket])
            session.flush()

            message = SupportTicketMessage(
                ticket_id=ticket.id,
                account_id=account.id,
                author_type="account",
                message_body="The support thread persisted correctly.",
                is_internal_note=False,
            )
            attachment = SupportTicketAttachment(
                ticket_id=ticket.id,
                uploaded_by_account_id=account.id,
                storage_key=f"support/{suffix}/evidence.txt",
                original_filename="evidence.txt",
                content_type="text/plain",
                file_size_bytes=128,
                scan_status="clean",
            )
            session.add_all([message, attachment])
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.addresses),
                    selectinload(Account.support_tickets).selectinload(SupportTicket.messages),
                    selectinload(Account.support_tickets).selectinload(SupportTicket.attachments),
                )
                .where(Account.id == account_id)
            )

            assert persisted_account is not None
            assert persisted_account.created_at is not None
            assert persisted_account.addresses[0].formatted_address == (
                "100 Integration Way, Austin, TX 78701, US"
            )
            assert persisted_account.addresses[0].is_primary is True

            persisted_ticket = persisted_account.support_tickets[0]
            assert persisted_ticket.ticket_code == f"TCK-{suffix}"
            assert persisted_ticket.status == "open"
            assert persisted_ticket.messages[0].message_body == (
                "The support thread persisted correctly."
            )
            assert persisted_ticket.attachments[0].storage_key == f"support/{suffix}/evidence.txt"
    finally:
        if account_id is not None:
            _cleanup_account(account_id)


def test_parent_profile_round_trip_persists_active_discord_linkage() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"profile_{suffix}",
                email=f"profile_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            profile = Profile(
                account_id=account.id,
                display_name="Discord Linked User",
                discord_user_id=f"discord-{suffix}",
                discord_username=f"discord_user_{suffix}",
                discord_integration_status="connected",
            )
            session.add(profile)
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(selectinload(Account.profile))
                .where(Account.id == account_id)
            )

            assert persisted_account is not None
            assert persisted_account.profile is not None
            assert persisted_account.profile.discord_user_id == f"discord-{suffix}"
            assert persisted_account.profile.discord_username == f"discord_user_{suffix}"
            assert persisted_account.profile.discord_integration_status == "connected"
    finally:
        if account_id is not None:
            _cleanup_account(account_id)


def test_parent_pay_projection_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None
    synced_at = datetime.now(timezone.utc).replace(microsecond=0)

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"projection_{suffix}",
                email=f"projection_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            subscription = SubscriptionSummary(
                account_id=account.id,
                product_code="parent-pro",
                plan_code="monthly",
                billing_interval="month",
                normalized_status="active",
                provider_status_raw="active",
                current_period_start_at=synced_at,
                current_period_end_at=synced_at,
                cancel_at_period_end=False,
                next_billing_at=synced_at,
                last_synced_at=synced_at,
            )
            payment = PaymentSummary(
                account_id=account.id,
                product_code="parent-pro",
                payment_rail="card",
                normalized_status="succeeded",
                provider_status_raw="paid",
                amount_cents=4900,
                currency="USD",
                paid_at=synced_at,
                provider_payment_reference=f"pi_{suffix}",
            )
            payment_method = PaymentMethodSummary(
                account_id=account.id,
                provider="stripe",
                provider_customer_id=f"cus_{suffix}",
                provider_payment_method_id=f"pm_{suffix}",
                brand="visa",
                last4="4242",
                exp_month=12,
                exp_year=2030,
                billing_name="Projection User",
                billing_country="US",
                is_default=True,
                status="active",
                last_synced_at=synced_at,
            )
            session.add_all([subscription, payment, payment_method])
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.subscription_summaries),
                    selectinload(Account.payment_summaries),
                    selectinload(Account.payment_method_summaries),
                )
                .where(Account.id == account_id)
            )

            assert persisted_account is not None
            assert persisted_account.subscription_summaries[0].normalized_status == "active"
            assert persisted_account.subscription_summaries[0].next_billing_at == synced_at
            assert persisted_account.payment_summaries[0].provider_payment_reference == f"pi_{suffix}"
            assert persisted_account.payment_summaries[0].amount_cents == 4900
            assert persisted_account.payment_method_summaries[0].provider == "stripe"
            assert persisted_account.payment_method_summaries[0].is_default is True
    finally:
        if account_id is not None:
            _cleanup_account(account_id)
