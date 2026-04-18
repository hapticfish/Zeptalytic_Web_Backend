from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.rewards.account_badges import AccountBadge
from app.db.models.rewards.account_objective_progress import AccountObjectiveProgress
from app.db.models.rewards.badge_definitions import BadgeDefinition
from app.db.models.rewards.objective_definitions import ObjectiveDefinition
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_definitions import RewardDefinition
from app.db.models.rewards.reward_events import RewardEvent
from app.db.models.rewards.reward_grants import RewardGrant
from app.db.models.rewards.reward_notifications import RewardNotification
from app.db.repositories.reward_progression_repository import RewardProgressionRepository


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
        RewardAccount.__table__,
        ObjectiveDefinition.__table__,
        AccountObjectiveProgress.__table__,
        RewardDefinition.__table__,
        BadgeDefinition.__table__,
        RewardEvent.__table__,
        RewardGrant.__table__,
        AccountBadge.__table__,
        RewardNotification.__table__,
    ):
        copied_table = table.to_metadata(metadata)
        for column in copied_table.c:
            if column.name == "metadata":
                column.server_default = None

    metadata.create_all(engine)
    return Session(engine)


def _create_account(session: Session, suffix: str = "progression") -> Account:
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


def test_reward_progression_repository_award_points_creates_event_and_snapshot() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "award")
    repository = RewardProgressionRepository(session)
    created_at = datetime(2026, 4, 16, 18, 10, tzinfo=timezone.utc)

    result = repository.award_points(
        account_id=account.id,
        event_type="objective_completed",
        points_delta=125,
        source_type="objective",
        source_reference="objective:onboarding",
        status="applied",
        created_at=created_at,
        metadata={"objective_code": "onboarding"},
    )

    assert result is not None
    assert result.reward_account.current_points == 125
    assert result.reward_account.current_tier == "BRONZE"
    assert result.reward_account.next_milestone_points == 200

    persisted_reward_account = session.get(RewardAccount, account.id)
    persisted_events = session.scalars(
        select(RewardEvent).where(RewardEvent.account_id == account.id)
    ).all()

    assert persisted_reward_account is not None
    assert persisted_reward_account.current_points == 125
    assert len(persisted_events) == 1
    assert persisted_events[0].event_metadata == {"objective_code": "onboarding"}


def test_reward_progression_repository_reverse_event_revokes_linked_rewards_and_badges() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "reverse")
    reward_definition = RewardDefinition(
        reward_code=f"reward_{uuid4().hex[:8]}",
        reward_type="cosmetic",
        display_name="Reward",
        description="Revocable reward.",
        is_repeatable=False,
        is_revocable=True,
        grant_mode="automatic",
        reward_metadata={},
    )
    badge_definition = BadgeDefinition(
        badge_code=f"badge_{uuid4().hex[:8]}",
        display_name="Badge",
        description="Revocable badge.",
        icon_ref=None,
        is_revocable=True,
        badge_metadata={},
    )
    session.add_all([reward_definition, badge_definition])
    session.commit()

    applied_event = RewardEvent(
        account_id=account.id,
        event_type="subscription_upgrade",
        points_delta=1000,
        reward_definition_id=reward_definition.id,
        badge_definition_id=badge_definition.id,
        source_type="subscription",
        source_reference="subscription:zardbot-pro",
        status="applied",
        event_metadata={},
    )
    reward_account = RewardAccount(
        account_id=account.id,
        current_points=1000,
        current_tier="SILVER",
        current_tier_progress_points=0,
        next_milestone_points=1100,
    )
    session.add_all([applied_event, reward_account])
    session.flush()

    reward_grant = RewardGrant(
        account_id=account.id,
        reward_definition_id=reward_definition.id,
        source_reward_event_id=applied_event.id,
        status="granted",
        grant_metadata={},
    )
    account_badge = AccountBadge(
        account_id=account.id,
        badge_definition_id=badge_definition.id,
        source_reward_event_id=applied_event.id,
        badge_metadata={},
    )
    session.add_all([reward_grant, account_badge])
    session.commit()

    repository = RewardProgressionRepository(session)
    reversed_at = datetime(2026, 4, 16, 18, 20, tzinfo=timezone.utc)
    result = repository.reverse_event(
        account_id=account.id,
        reversed_event_id=applied_event.id,
        event_type="subscription_upgrade_reversed",
        source_type="manual_review",
        source_reference="review:retention-window",
        status="reversed",
        created_at=reversed_at,
        metadata={"reason": "retention_requirement_failed"},
        revocation_reason="retention_requirement_failed",
    )

    assert result is not None
    assert result.is_reversal is True
    assert result.reward_account.current_points == 0
    assert result.revoked_reward_grant_ids == [reward_grant.id]
    assert result.revoked_badge_ids == [account_badge.id]

    persisted_grant = session.get(RewardGrant, reward_grant.id)
    persisted_badge = session.get(AccountBadge, account_badge.id)
    assert persisted_grant is not None
    assert persisted_badge is not None
    assert persisted_grant.status == "revoked"
    assert persisted_grant.revocation_reason == "retention_requirement_failed"
    assert persisted_badge.revocation_reason == "retention_requirement_failed"


def test_reward_progression_repository_complete_objective_handles_repeatable_rollover() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "objective")
    objective = ObjectiveDefinition(
        objective_code=f"repeatable_{uuid4().hex[:8]}",
        title="Repeatable Objective",
        description="Tracks repeatable completion cycles.",
        scope_type="global",
        product_code=None,
        objective_type="engagement",
        is_repeatable=True,
        repeat_group_key="repeatable_group",
        required_count=3,
        tier_gate=None,
        subscription_gate_product_code=None,
        subscription_gate_plan_code=None,
        is_milestone_objective=False,
        sort_group="repeatable",
        sort_order=1,
        active=True,
        objective_metadata={},
    )
    session.add(objective)
    session.commit()

    repository = RewardProgressionRepository(session)
    progress_at = datetime(2026, 4, 16, 18, 30, tzinfo=timezone.utc)

    first_update = repository.complete_objective(
        account_id=account.id,
        objective_definition_id=objective.id,
        increment_by=2,
        progress_at=progress_at,
        metadata={"recent_action": "launcher_opened"},
    )
    second_update = repository.complete_objective(
        account_id=account.id,
        objective_definition_id=objective.id,
        increment_by=2,
        progress_at=progress_at,
        metadata={"last_completed_iteration": 1},
    )

    assert first_update is not None
    assert second_update is not None
    assert first_update.status == "in_progress"
    assert first_update.current_count == 2
    assert first_update.completed_now is False
    assert second_update.completed_now is True
    assert second_update.completed_count == 1
    assert second_update.repeat_iteration == 2
    assert second_update.current_count == 1
    assert second_update.metadata == {
        "recent_action": "launcher_opened",
        "last_completed_iteration": 1,
    }


def test_reward_progression_repository_queue_notification_appends_sequence_order() -> None:
    session = _create_in_memory_session()
    account = _create_account(session, "queue")
    repository = RewardProgressionRepository(session)
    queued_at = datetime(2026, 4, 16, 18, 40, tzinfo=timezone.utc)

    first_notification = repository.queue_notification(
        account_id=account.id,
        notification_type="objective_completion_queue",
        queued_at=queued_at,
        metadata={"queue_sequence": 1},
    )
    second_notification = repository.queue_notification(
        account_id=account.id,
        notification_type="objective_completion_queue",
        queued_at=queued_at,
        metadata={"queue_sequence": 2},
    )

    assert first_notification is not None
    assert second_notification is not None
    assert first_notification.sequence_order == 1
    assert second_notification.sequence_order == 2

    persisted_notifications = session.scalars(
        select(RewardNotification)
        .where(RewardNotification.account_id == account.id)
        .order_by(RewardNotification.sequence_order)
    ).all()
    assert [notification.sequence_order for notification in persisted_notifications] == [1, 2]
