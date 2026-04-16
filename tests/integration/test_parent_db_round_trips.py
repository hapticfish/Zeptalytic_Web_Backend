from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.accounts import Account
from app.db.models.addresses import Address
from app.db.models.discord_connection_history import DiscordConnectionHistory
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.profiles import Profile
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
from app.db.models.rewards.reward_tier_definitions import RewardTierDefinition
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
            history_entry = DiscordConnectionHistory(
                account_id=account.id,
                discord_user_id=f"discord-{suffix}",
                discord_username=f"discord_user_{suffix}",
                status="connected",
            )
            session.add_all([profile, history_entry])
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.profile),
                    selectinload(Account.discord_connection_history),
                )
                .where(Account.id == account_id)
            )

            assert persisted_account is not None
            assert persisted_account.profile is not None
            assert persisted_account.profile.discord_user_id == f"discord-{suffix}"
            assert persisted_account.profile.discord_username == f"discord_user_{suffix}"
            assert persisted_account.profile.discord_integration_status == "connected"
            assert len(persisted_account.discord_connection_history) == 1
            assert persisted_account.discord_connection_history[0].discord_user_id == f"discord-{suffix}"
            assert persisted_account.discord_connection_history[0].status == "connected"
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


def test_parent_rewards_foundation_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"reward_{suffix}",
                email=f"reward_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            reward_account = RewardAccount(
                account_id=account.id,
                current_points=100,
                current_tier="BRONZE",
                current_tier_progress_points=100,
                next_milestone_points=200,
            )
            first_event = RewardEvent(
                account_id=account.id,
                event_type="objective_completed",
                points_delta=100,
                source_type="objective",
                source_reference="objective:first-login",
                status="applied",
                event_metadata={"objective_code": "first-login"},
            )
            session.add_all([reward_account, first_event])
            session.flush()

            reversal_event = RewardEvent(
                account_id=account.id,
                event_type="objective_reversed",
                points_delta=-100,
                source_type="manual_review",
                source_reference="review:first-login",
                is_reversal=True,
                reversed_event_id=first_event.id,
                status="reversed",
                event_metadata={"reason": "qualification_window_failed"},
            )
            session.add(reversal_event)
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.reward_account),
                    selectinload(Account.reward_events),
                )
                .where(Account.id == account_id)
            )

            assert persisted_account is not None
            assert persisted_account.reward_account is not None
            assert persisted_account.reward_account.current_points == 100
            assert persisted_account.reward_account.current_tier == "BRONZE"
            assert persisted_account.reward_account.next_milestone_points == 200
            assert len(persisted_account.reward_events) == 2

            event_by_type = {event.event_type: event for event in persisted_account.reward_events}
            assert event_by_type["objective_completed"].event_metadata == {"objective_code": "first-login"}
            assert event_by_type["objective_reversed"].is_reversal is True
            assert event_by_type["objective_reversed"].reversed_event_id == event_by_type["objective_completed"].id
    finally:
        if account_id is not None:
            _cleanup_account(account_id)


def test_parent_rewards_tier_and_milestone_definitions_round_trip() -> None:
    with SessionLocal() as session:
        milestone_objectives = session.scalars(
            select(ObjectiveDefinition)
            .where(ObjectiveDefinition.is_milestone_objective.is_(True))
            .order_by(ObjectiveDefinition.sort_order)
        ).all()
        tiers = session.scalars(
            select(RewardTierDefinition).order_by(RewardTierDefinition.sort_order)
        ).all()
        milestones = session.scalars(
            select(RewardMilestone).order_by(RewardMilestone.sort_order)
        ).all()

    assert [tier.display_name for tier in tiers] == [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Plus",
    ]
    assert milestone_objectives[0].objective_metadata == {
        "milestone_points": 100,
        "tier_code": "BRONZE",
        "is_tier_boundary": False,
    }
    assert milestones[0].tier_code == "BRONZE"
    assert milestones[0].linked_objective_definition_id == milestone_objectives[0].id
    assert milestones[8].milestone_points == 900
    assert milestones[9].tier_code == "BRONZE"
    assert milestones[9].is_tier_boundary is True
    assert milestones[10].tier_code == "SILVER"
    assert milestones[49].tier_code == "PLUS"


def test_parent_objective_definition_and_progress_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None
    objective_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"objective_{suffix}",
                email=f"objective_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            session.add(account)
            session.flush()
            account_id = account.id

            objective = ObjectiveDefinition(
                objective_code=f"zardbot_session_{suffix}",
                title="Launch ZardBot Three Times",
                description="Track repeated ZardBot session launches for rewards progress.",
                scope_type="product",
                product_code="zardbot",
                objective_type="usage",
                is_repeatable=True,
                repeat_group_key="zardbot_sessions",
                required_count=3,
                tier_gate="SILVER",
                subscription_gate_product_code="zardbot",
                subscription_gate_plan_code="pro_monthly",
                is_milestone_objective=False,
                sort_group="product",
                sort_order=900,
                active=True,
                objective_metadata={"page": "objectives"},
            )
            session.add(objective)
            session.flush()
            objective_id = objective.id

            progress = AccountObjectiveProgress(
                account_id=account.id,
                objective_definition_id=objective.id,
                current_count=2,
                completed_count=0,
                repeat_iteration=1,
                status="in_progress",
                progress_metadata={"recent_action": "launcher_opened"},
            )
            session.add(progress)
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.account_objective_progress_entries).selectinload(
                        AccountObjectiveProgress.objective_definition
                    )
                )
                .where(Account.id == account_id)
            )

            persisted_objective = session.get(ObjectiveDefinition, objective_id)

            assert persisted_account is not None
            assert persisted_objective is not None
            assert len(persisted_account.account_objective_progress_entries) == 1

            persisted_progress = persisted_account.account_objective_progress_entries[0]
            assert persisted_progress.current_count == 2
            assert persisted_progress.repeat_iteration == 1
            assert persisted_progress.progress_metadata == {"recent_action": "launcher_opened"}
            assert persisted_progress.objective_definition.objective_code == f"zardbot_session_{suffix}"
            assert persisted_objective.scope_type == "product"
            assert persisted_objective.product_code == "zardbot"
            assert persisted_objective.subscription_gate_plan_code == "pro_monthly"
            assert persisted_objective.is_repeatable is True
    finally:
        with SessionLocal() as session:
            if objective_id is not None:
                objective = session.get(ObjectiveDefinition, objective_id)
                if objective is not None:
                    session.delete(objective)
                    session.commit()
        if account_id is not None:
            _cleanup_account(account_id)


def test_parent_reward_catalog_and_achievement_round_trip() -> None:
    suffix = _unique_suffix()
    account_id: UUID | None = None
    objective_id: UUID | None = None
    reward_definition_id: UUID | None = None
    badge_definition_id: UUID | None = None

    try:
        with SessionLocal() as session:
            account = Account(
                username=f"grant_{suffix}",
                email=f"grant_{suffix}@example.com",
                password_hash="hashed-password",
                status="active",
                role="member",
            )
            objective = ObjectiveDefinition(
                objective_code=f"objective_reward_{suffix}",
                title="Earn a Catalog Reward",
                description="Round-trip a linked objective reward and badge grant.",
                scope_type="product",
                product_code="zardbot",
                objective_type="engagement",
                is_repeatable=False,
                repeat_group_key=None,
                required_count=1,
                tier_gate="BRONZE",
                subscription_gate_product_code=None,
                subscription_gate_plan_code=None,
                is_milestone_objective=False,
                sort_group="product",
                sort_order=1500,
                active=True,
                objective_metadata={"channel": "objectives"},
            )
            reward_definition = RewardDefinition(
                reward_code=f"cosmetic_{suffix}",
                reward_type="cosmetic",
                display_name="Founders Frame",
                description="Unlock a cosmetic frame.",
                is_repeatable=False,
                is_revocable=True,
                grant_mode="automatic",
                reward_metadata={"rarity": "limited"},
            )
            badge_definition = BadgeDefinition(
                badge_code=f"badge_{suffix}",
                display_name="Founders Badge",
                description="Marks the first catalog achievement.",
                icon_ref="badges/founders.svg",
                is_revocable=True,
                badge_metadata={"family": "founders"},
            )
            session.add_all([account, objective, reward_definition, badge_definition])
            session.flush()
            account_id = account.id
            objective_id = objective.id
            reward_definition_id = reward_definition.id
            badge_definition_id = badge_definition.id

            event = RewardEvent(
                account_id=account.id,
                event_type="objective_completed",
                points_delta=0,
                objective_definition_id=objective.id,
                reward_definition_id=reward_definition.id,
                badge_definition_id=badge_definition.id,
                source_type="objective",
                source_reference=f"objective:{objective.objective_code}",
                status="applied",
                event_metadata={"reason": "catalog_unlock"},
            )
            session.add(event)
            session.flush()

            link = ObjectiveRewardLink(
                objective_definition_id=objective.id,
                reward_definition_id=reward_definition.id,
                grant_order=1,
            )
            grant = RewardGrant(
                account_id=account.id,
                reward_definition_id=reward_definition.id,
                source_objective_definition_id=objective.id,
                source_reward_event_id=event.id,
                status="granted",
                grant_metadata={"surface": "objectives_page"},
            )
            badge = AccountBadge(
                account_id=account.id,
                badge_definition_id=badge_definition.id,
                source_objective_definition_id=objective.id,
                source_reward_event_id=event.id,
                badge_metadata={"surface": "rewards_gallery"},
            )
            session.add_all([link, grant, badge])
            session.commit()

        with SessionLocal() as session:
            persisted_account = session.scalar(
                select(Account)
                .options(
                    selectinload(Account.reward_grants).selectinload(RewardGrant.reward_definition),
                    selectinload(Account.account_badges).selectinload(AccountBadge.badge_definition),
                    selectinload(Account.reward_events).selectinload(RewardEvent.reward_definition),
                    selectinload(Account.reward_events).selectinload(RewardEvent.badge_definition),
                )
                .where(Account.id == account_id)
            )
            persisted_objective = session.scalar(
                select(ObjectiveDefinition)
                .options(
                    selectinload(ObjectiveDefinition.objective_reward_links).selectinload(
                        ObjectiveRewardLink.reward_definition
                    )
                )
                .where(ObjectiveDefinition.id == objective_id)
            )

            assert persisted_account is not None
            assert persisted_objective is not None
            assert len(persisted_account.reward_grants) == 1
            assert persisted_account.reward_grants[0].status == "granted"
            assert persisted_account.reward_grants[0].grant_metadata == {"surface": "objectives_page"}
            assert persisted_account.reward_grants[0].reward_definition.reward_code == f"cosmetic_{suffix}"
            assert len(persisted_account.account_badges) == 1
            assert persisted_account.account_badges[0].badge_metadata == {
                "surface": "rewards_gallery"
            }
            assert persisted_account.account_badges[0].badge_definition.badge_code == f"badge_{suffix}"
            assert persisted_account.reward_events[0].reward_definition is not None
            assert persisted_account.reward_events[0].badge_definition is not None
            assert persisted_objective.objective_reward_links[0].grant_order == 1
            assert (
                persisted_objective.objective_reward_links[0].reward_definition.display_name
                == "Founders Frame"
            )
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
        if account_id is not None:
            _cleanup_account(account_id)
