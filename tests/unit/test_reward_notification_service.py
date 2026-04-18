from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.reward_notification_repository import (
    RewardNotificationBadgeRecord,
    RewardNotificationEventRecord,
    RewardNotificationObjectiveRecord,
    RewardNotificationQueueRecord,
    RewardNotificationRecord,
    RewardNotificationRewardRecord,
    RewardNotificationSkipAllRecord,
    RewardNotificationStateChangeRecord,
)
from app.services.reward_notification_service import (
    RewardNotificationNotFoundError,
    RewardNotificationService,
)


class StubRewardNotificationRepository:
    def __init__(
        self,
        queue_record: RewardNotificationQueueRecord | None,
        state_change_record: RewardNotificationStateChangeRecord | None,
        skip_all_record: RewardNotificationSkipAllRecord | None,
    ) -> None:
        self._queue_record = queue_record
        self._state_change_record = state_change_record
        self._skip_all_record = skip_all_record

    def get_notification_queue(self, account_id):  # noqa: ANN001
        return self._queue_record

    def mark_notification_seen(self, account_id, notification_id, seen_at):  # noqa: ANN001
        return self._state_change_record

    def skip_all_notifications(self, account_id, skipped_at):  # noqa: ANN001
        return self._skip_all_record


def _build_notification_record() -> RewardNotificationRecord:
    queued_at = datetime(2026, 4, 16, 16, 0, tzinfo=timezone.utc)
    created_at = datetime(2026, 4, 16, 15, 59, tzinfo=timezone.utc)
    return RewardNotificationRecord(
        notification_id=uuid4(),
        notification_type="objective_completion_queue",
        status="queued",
        queued_at=queued_at,
        seen_at=None,
        dismissed_at=None,
        sequence_order=1,
        metadata={"entry_surface": "objectives_page"},
        objective=RewardNotificationObjectiveRecord(
            objective_definition_id=uuid4(),
            objective_code="complete_profile",
            title="Complete Your Profile",
            is_milestone_objective=False,
        ),
        reward=RewardNotificationRewardRecord(
            reward_definition_id=uuid4(),
            reward_code="profile-badge",
            reward_type="cosmetic",
            display_name="Profile Badge",
            description="Unlock the profile completion badge.",
            granted_at=queued_at,
        ),
        badge=RewardNotificationBadgeRecord(
            badge_definition_id=uuid4(),
            badge_code="profile-complete",
            display_name="Profile Complete",
            description="Finished the profile setup objective.",
            icon_ref="badges/profile-complete.svg",
        ),
        reward_event=RewardNotificationEventRecord(
            reward_event_id=uuid4(),
            event_type="objective_completed",
            points_delta=100,
            source_type="objective",
            source_reference="objective:complete_profile",
            created_at=created_at,
            metadata={"entry_surface": "objectives_page"},
        ),
    )


def test_reward_notification_service_returns_queue_payload() -> None:
    account_id = uuid4()
    service = RewardNotificationService(
        StubRewardNotificationRepository(
            queue_record=RewardNotificationQueueRecord(
                account_id=account_id,
                notifications=[_build_notification_record()],
            ),
            state_change_record=None,
            skip_all_record=None,
        )
    )

    response = service.get_notification_queue(account_id)

    assert response.account_id == account_id
    assert response.notifications[0].notification_type == "objective_completion_queue"
    assert response.notifications[0].objective is not None
    assert response.notifications[0].objective.objective_code == "complete_profile"
    assert response.notifications[0].reward_event is not None
    assert response.notifications[0].reward_event.points_delta == 100


def test_reward_notification_service_raises_for_missing_account_queue() -> None:
    service = RewardNotificationService(
        StubRewardNotificationRepository(
            queue_record=None,
            state_change_record=None,
            skip_all_record=None,
        )
    )

    try:
        service.get_notification_queue(uuid4())
    except RewardNotificationNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing queue to raise RewardNotificationNotFoundError")


def test_reward_notification_service_returns_seen_transition_payload() -> None:
    account_id = uuid4()
    notification = _build_notification_record()
    notification.status = "seen"
    notification.seen_at = datetime(2026, 4, 16, 16, 1, tzinfo=timezone.utc)
    service = RewardNotificationService(
        StubRewardNotificationRepository(
            queue_record=None,
            state_change_record=RewardNotificationStateChangeRecord(
                account_id=account_id,
                notification=notification,
                pending_notifications_remaining=2,
            ),
            skip_all_record=None,
        )
    )

    response = service.mark_notification_seen(account_id, notification.notification_id)

    assert response.account_id == account_id
    assert response.notification.status == "seen"
    assert response.pending_notifications_remaining == 2


def test_reward_notification_service_returns_skip_all_summary() -> None:
    account_id = uuid4()
    dismissed_notification_ids = [uuid4(), uuid4()]
    skipped_at = datetime(2026, 4, 16, 16, 2, tzinfo=timezone.utc)
    service = RewardNotificationService(
        StubRewardNotificationRepository(
            queue_record=None,
            state_change_record=None,
            skip_all_record=RewardNotificationSkipAllRecord(
                account_id=account_id,
                dismissed_notification_ids=dismissed_notification_ids,
                dismissed_count=2,
                skipped_at=skipped_at,
            ),
        )
    )

    response = service.skip_all_notifications(account_id)

    assert response.account_id == account_id
    assert response.dismissed_notification_ids == dismissed_notification_ids
    assert response.dismissed_count == 2
    assert response.skipped_at == skipped_at
