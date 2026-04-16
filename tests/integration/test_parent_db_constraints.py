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
from app.db.models.rewards.account_badges import AccountBadge
from app.db.models.rewards.account_objective_progress import AccountObjectiveProgress
from app.db.models.rewards.badge_definitions import BadgeDefinition
from app.db.models.rewards.objective_definitions import ObjectiveDefinition
from app.db.models.rewards.objective_reward_links import ObjectiveRewardLink
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_definitions import RewardDefinition
from app.db.models.rewards.reward_events import RewardEvent
from app.db.models.rewards.reward_grants import RewardGrant
from app.db.models.rewards.reward_milestones import RewardMilestone
from app.db.models.rewards.reward_notifications import RewardNotification
from app.db.models.rewards.reward_tier_definitions import RewardTierDefinition
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


def test_parent_db_reward_definition_seed_contract_and_indexes_exist() -> None:
    with SessionLocal() as session:
        objective_definitions = session.query(ObjectiveDefinition).order_by(
            ObjectiveDefinition.sort_order
        ).all()
        tiers = session.query(RewardTierDefinition).order_by(RewardTierDefinition.sort_order).all()
        milestones = session.query(RewardMilestone).order_by(RewardMilestone.sort_order).all()

    milestone_objectives = [
        objective for objective in objective_definitions if objective.is_milestone_objective
    ]

    assert [tier.tier_code for tier in tiers] == [
        "BRONZE",
        "SILVER",
        "GOLD",
        "PLATINUM",
        "PLUS",
    ]
    assert [(tier.tier_start_points, tier.tier_end_points) for tier in tiers] == [
        (0, 999),
        (1000, 1999),
        (2000, 2999),
        (3000, 3999),
        (4000, 4999),
    ]
    assert len(milestones) == 50
    assert milestones[0].milestone_points == 100
    assert milestones[-1].milestone_points == 5000
    assert len(milestone_objectives) == 50
    assert milestone_objectives[0].objective_code == "milestone_0100"
    assert milestone_objectives[-1].objective_code == "milestone_5000"
    assert [milestone.milestone_points for milestone in milestones if milestone.is_tier_boundary] == [
        1000,
        2000,
        3000,
        4000,
        5000,
    ]
    assert all(milestone.linked_objective_definition_id is not None for milestone in milestones)

    inspector = inspect(engine)
    objective_definition_indexes = {
        index["name"] for index in inspector.get_indexes("objective_definitions")
    }
    objective_progress_indexes = {
        index["name"] for index in inspector.get_indexes("account_objective_progress")
    }
    reward_tier_indexes = {
        index["name"] for index in inspector.get_indexes("reward_tier_definitions")
    }
    reward_milestone_indexes = {
        index["name"] for index in inspector.get_indexes("reward_milestones")
    }

    assert "ix_objective_definitions_scope_type" in objective_definition_indexes
    assert "ix_objective_definitions_sort_group_sort_order" in objective_definition_indexes
    assert "uq_objective_definitions_objective_code" in objective_definition_indexes
    assert "ix_account_objective_progress_account_id" in objective_progress_indexes
    assert "ix_account_objective_progress_objective_definition_id" in objective_progress_indexes
    assert "ix_account_objective_progress_status" in objective_progress_indexes
    assert "ix_reward_tier_definitions_sort_order" in reward_tier_indexes
    assert "uq_reward_tier_definitions_tier_code" in reward_tier_indexes
    assert "ix_reward_milestones_sort_order" in reward_milestone_indexes
    assert "uq_reward_milestones_milestone_points" in reward_milestone_indexes


def test_parent_db_account_objective_progress_requires_existing_account_and_objective() -> None:
    with SessionLocal() as session:
        session.add(
            AccountObjectiveProgress(
                account_id=uuid4(),
                objective_definition_id=uuid4(),
                status="in_progress",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()


def test_parent_db_reward_catalog_and_achievement_constraints_exist() -> None:
    account_ids: list[UUID] = []
    objective_id: UUID | None = None
    reward_definition_id: UUID | None = None
    badge_definition_id: UUID | None = None
    suffix = _unique_suffix()

    try:
        with SessionLocal() as session:
            account = _build_account(suffix)
            objective = ObjectiveDefinition(
                objective_code=f"catalog_objective_{suffix}",
                title="Complete Rewards Catalog Objective",
                description="Verifies reward/badge catalog constraints in Postgres.",
                scope_type="global",
                product_code=None,
                objective_type="engagement",
                is_repeatable=False,
                repeat_group_key=None,
                required_count=1,
                tier_gate=None,
                subscription_gate_product_code=None,
                subscription_gate_plan_code=None,
                is_milestone_objective=False,
                sort_group="catalog",
                sort_order=1200,
                active=True,
                objective_metadata={"source": "constraints"},
            )
            reward_definition = RewardDefinition(
                reward_code=f"reward_{suffix}",
                reward_type="cosmetic",
                display_name="Catalog Reward",
                description="A reward used for constraint verification.",
                is_repeatable=False,
                is_revocable=True,
                grant_mode="automatic",
                reward_metadata={"origin": "constraints"},
            )
            badge_definition = BadgeDefinition(
                badge_code=f"badge_{suffix}",
                display_name="Catalog Badge",
                description="A badge used for constraint verification.",
                icon_ref="badges/catalog.svg",
                is_revocable=True,
                badge_metadata={"origin": "constraints"},
            )
            session.add_all([account, objective, reward_definition, badge_definition])
            session.commit()

            account_ids.append(account.id)
            objective_id = objective.id
            reward_definition_id = reward_definition.id
            badge_definition_id = badge_definition.id

            session.add(
                ObjectiveRewardLink(
                    objective_definition_id=objective.id,
                    reward_definition_id=reward_definition.id,
                    grant_order=1,
                )
            )
            session.commit()

            session.add(
                ObjectiveRewardLink(
                    objective_definition_id=objective.id,
                    reward_definition_id=reward_definition.id,
                    grant_order=2,
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

        with SessionLocal() as session:
            session.add(
                RewardGrant(
                    account_id=uuid4(),
                    reward_definition_id=reward_definition_id or uuid4(),
                    source_objective_definition_id=objective_id,
                    status="granted",
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

            session.add(
                AccountBadge(
                    account_id=account_ids[0],
                    badge_definition_id=uuid4(),
                    source_objective_definition_id=objective_id,
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

            session.add(
                RewardEvent(
                    account_id=account_ids[0],
                    event_type="reward_granted",
                    points_delta=0,
                    objective_definition_id=objective_id,
                    reward_definition_id=reward_definition_id,
                    badge_definition_id=badge_definition_id,
                    source_type="objective",
                    source_reference=f"objective:{suffix}",
                    status="applied",
                )
            )
            session.commit()

        inspector = inspect(engine)
        reward_definition_indexes = {
            index["name"] for index in inspector.get_indexes("reward_definitions")
        }
        objective_reward_link_indexes = {
            index["name"] for index in inspector.get_indexes("objective_reward_links")
        }
        reward_grant_indexes = {index["name"] for index in inspector.get_indexes("reward_grants")}
        badge_definition_indexes = {
            index["name"] for index in inspector.get_indexes("badge_definitions")
        }
        account_badge_indexes = {index["name"] for index in inspector.get_indexes("account_badges")}
        reward_event_fks = {
            fk["name"] for fk in inspector.get_foreign_keys("reward_events") if fk["name"]
        }

        assert "ix_reward_definitions_reward_type" in reward_definition_indexes
        assert "uq_reward_definitions_reward_code" in reward_definition_indexes
        assert "ix_objective_reward_links_objective_definition_id" in objective_reward_link_indexes
        assert "ix_objective_reward_links_reward_definition_id" in objective_reward_link_indexes
        assert "uq_objective_reward_links_objective_reward" in objective_reward_link_indexes
        assert "ix_reward_grants_account_id" in reward_grant_indexes
        assert "ix_reward_grants_reward_definition_id" in reward_grant_indexes
        assert "ix_reward_grants_status" in reward_grant_indexes
        assert "ix_badge_definitions_display_name" in badge_definition_indexes
        assert "uq_badge_definitions_badge_code" in badge_definition_indexes
        assert "ix_account_badges_account_id" in account_badge_indexes
        assert "ix_account_badges_badge_definition_id" in account_badge_indexes
        assert "fk_reward_events_objective_definition" in reward_event_fks
        assert "fk_reward_events_reward_definition" in reward_event_fks
        assert "fk_reward_events_badge_definition" in reward_event_fks
    finally:
        with SessionLocal() as session:
            if objective_id is not None:
                objective = session.get(ObjectiveDefinition, objective_id)
                if objective is not None:
                    session.delete(objective)
            if reward_definition_id is not None:
                reward_definition = session.get(RewardDefinition, reward_definition_id)
                if reward_definition is not None:
                    session.delete(reward_definition)
            if badge_definition_id is not None:
                badge_definition = session.get(BadgeDefinition, badge_definition_id)
                if badge_definition is not None:
                    session.delete(badge_definition)
            session.commit()
        _cleanup_accounts(account_ids)


def test_parent_db_reward_notifications_require_existing_related_rows_and_indexes_exist() -> None:
    account_ids: list[UUID] = []
    objective_id: UUID | None = None
    reward_definition_id: UUID | None = None
    reward_grant_id: UUID | None = None
    reward_event_id: UUID | None = None
    badge_definition_id: UUID | None = None
    suffix = _unique_suffix()

    try:
        with SessionLocal() as session:
            account = _build_account(suffix)
            objective = ObjectiveDefinition(
                objective_code=f"notification_objective_{suffix}",
                title="Queue a reward notification",
                description="Verifies reward notification constraints in Postgres.",
                scope_type="global",
                product_code=None,
                objective_type="engagement",
                is_repeatable=False,
                repeat_group_key=None,
                required_count=1,
                tier_gate=None,
                subscription_gate_product_code=None,
                subscription_gate_plan_code=None,
                is_milestone_objective=False,
                sort_group="notifications",
                sort_order=1700,
                active=True,
                objective_metadata={"source": "constraints"},
            )
            reward_definition = RewardDefinition(
                reward_code=f"reward_notification_{suffix}",
                reward_type="milestone_reward",
                display_name="Queued Reward",
                description="A queued reward used for reward-notification verification.",
                is_repeatable=False,
                is_revocable=True,
                grant_mode="automatic",
                reward_metadata={"origin": "constraints"},
            )
            badge_definition = BadgeDefinition(
                badge_code=f"badge_notification_{suffix}",
                display_name="Queued Badge",
                description="A queued badge used for reward-notification verification.",
                icon_ref="badges/queued.svg",
                is_revocable=True,
                badge_metadata={"origin": "constraints"},
            )
            session.add_all([account, objective, reward_definition, badge_definition])
            session.flush()

            reward_event = RewardEvent(
                account_id=account.id,
                event_type="objective_completed",
                points_delta=100,
                objective_definition_id=objective.id,
                reward_definition_id=reward_definition.id,
                badge_definition_id=badge_definition.id,
                source_type="objective",
                source_reference=f"objective:{objective.objective_code}",
                status="applied",
            )
            session.add(reward_event)
            session.flush()

            reward_grant = RewardGrant(
                account_id=account.id,
                reward_definition_id=reward_definition.id,
                source_objective_definition_id=objective.id,
                source_reward_event_id=reward_event.id,
                status="granted",
            )
            session.add(reward_grant)
            session.commit()

            account_ids.append(account.id)
            objective_id = objective.id
            reward_definition_id = reward_definition.id
            reward_grant_id = reward_grant.id
            reward_event_id = reward_event.id
            badge_definition_id = badge_definition.id

        with SessionLocal() as session:
            session.add(
                RewardNotification(
                    account_id=uuid4(),
                    notification_type="objective_completion_queue",
                    objective_definition_id=objective_id,
                    reward_grant_id=reward_grant_id,
                    badge_definition_id=badge_definition_id,
                    reward_event_id=reward_event_id,
                    status="queued",
                    sequence_order=1,
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

            session.add(
                RewardNotification(
                    account_id=account_ids[0],
                    notification_type="objective_completion_queue",
                    objective_definition_id=uuid4(),
                    reward_grant_id=reward_grant_id,
                    badge_definition_id=badge_definition_id,
                    reward_event_id=reward_event_id,
                    status="queued",
                    sequence_order=2,
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()

            session.rollback()

        inspector = inspect(engine)
        reward_notification_indexes = {
            index["name"] for index in inspector.get_indexes("reward_notifications")
        }

        assert "ix_reward_notifications_account_id" in reward_notification_indexes
        assert "ix_reward_notifications_status" in reward_notification_indexes
        assert "ix_reward_notifications_sequence_order" in reward_notification_indexes
    finally:
        with SessionLocal() as session:
            if objective_id is not None:
                objective = session.get(ObjectiveDefinition, objective_id)
                if objective is not None:
                    session.delete(objective)
            if reward_definition_id is not None:
                reward_definition = session.get(RewardDefinition, reward_definition_id)
                if reward_definition is not None:
                    session.delete(reward_definition)
            if badge_definition_id is not None:
                badge_definition = session.get(BadgeDefinition, badge_definition_id)
                if badge_definition is not None:
                    session.delete(badge_definition)
            session.commit()
        _cleanup_accounts(account_ids)
