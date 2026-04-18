from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.repositories.reward_progression_repository import (
    ObjectiveProgressUpdateRecord,
    RewardAccountSnapshotRecord,
    RewardEventApplicationRecord,
    RewardNotificationQueueRecord,
)
from app.services.reward_progression_service import (
    ObjectiveCompletionCommand,
    RewardNotificationQueueCommand,
    RewardPointsAwardCommand,
    RewardPointsReversalCommand,
    RewardProgressionNotFoundError,
    RewardProgressionService,
)


class StubRewardProgressionRepository:
    def __init__(
        self,
        *,
        award_result: RewardEventApplicationRecord | None = None,
        reversal_result: RewardEventApplicationRecord | None = None,
        objective_result: ObjectiveProgressUpdateRecord | None = None,
        queue_result: RewardNotificationQueueRecord | None = None,
    ) -> None:
        self.award_result = award_result
        self.reversal_result = reversal_result
        self.objective_result = objective_result
        self.queue_result = queue_result
        self.last_call: tuple[str, dict[str, object]] | None = None

    def award_points(self, **kwargs):  # noqa: ANN003
        self.last_call = ("award_points", kwargs)
        return self.award_result

    def reverse_event(self, **kwargs):  # noqa: ANN003
        self.last_call = ("reverse_event", kwargs)
        return self.reversal_result

    def complete_objective(self, **kwargs):  # noqa: ANN003
        self.last_call = ("complete_objective", kwargs)
        return self.objective_result

    def queue_notification(self, **kwargs):  # noqa: ANN003
        self.last_call = ("queue_notification", kwargs)
        return self.queue_result


def _build_snapshot(account_id):  # noqa: ANN001
    return RewardAccountSnapshotRecord(
        account_id=account_id,
        current_points=250,
        current_tier="BRONZE",
        current_tier_progress_points=250,
        next_milestone_points=300,
        last_recomputed_at=datetime(2026, 4, 16, 18, 0, tzinfo=timezone.utc),
    )


def test_reward_progression_service_award_points_injects_timestamp_and_returns_record() -> None:
    account_id = uuid4()
    repository = StubRewardProgressionRepository(
        award_result=RewardEventApplicationRecord(
            event_id=uuid4(),
            account_id=account_id,
            event_type="objective_completed",
            points_delta=250,
            is_reversal=False,
            reversed_event_id=None,
            status="applied",
            source_type="objective",
            source_reference="objective:welcome",
            created_at=datetime(2026, 4, 16, 18, 0, tzinfo=timezone.utc),
            metadata={"objective_code": "welcome"},
            reward_account=_build_snapshot(account_id),
            revoked_reward_grant_ids=[],
            revoked_badge_ids=[],
        )
    )
    service = RewardProgressionService(repository)

    result = service.award_points(
        RewardPointsAwardCommand(
            account_id=account_id,
            event_type="objective_completed",
            points_delta=250,
            source_type="objective",
            source_reference="objective:welcome",
            metadata={"objective_code": "welcome"},
        )
    )

    assert result.account_id == account_id
    assert repository.last_call is not None
    assert repository.last_call[0] == "award_points"
    assert isinstance(repository.last_call[1]["created_at"], datetime)


def test_reward_progression_service_reverse_points_raises_for_missing_event() -> None:
    service = RewardProgressionService(StubRewardProgressionRepository(reversal_result=None))

    with pytest.raises(RewardProgressionNotFoundError):
        service.reverse_points(
            RewardPointsReversalCommand(
                account_id=uuid4(),
                reversed_event_id=uuid4(),
                event_type="objective_reversed",
                source_type="manual_review",
            )
        )


def test_reward_progression_service_reverse_points_forwards_command_fields() -> None:
    account_id = uuid4()
    reversed_event_id = uuid4()
    created_at = datetime(2026, 4, 16, 18, 2, tzinfo=timezone.utc)
    repository = StubRewardProgressionRepository(
        reversal_result=RewardEventApplicationRecord(
            event_id=uuid4(),
            account_id=account_id,
            event_type="objective_reversed",
            points_delta=-250,
            is_reversal=True,
            reversed_event_id=reversed_event_id,
            status="reversed",
            source_type="manual_review",
            source_reference="review:retention-window",
            created_at=created_at,
            metadata={"reason": "retention_requirement_failed"},
            reward_account=_build_snapshot(account_id),
            revoked_reward_grant_ids=[uuid4()],
            revoked_badge_ids=[uuid4()],
        )
    )
    service = RewardProgressionService(repository)

    result = service.reverse_points(
        RewardPointsReversalCommand(
            account_id=account_id,
            reversed_event_id=reversed_event_id,
            event_type="objective_reversed",
            source_type="manual_review",
            source_reference="review:retention-window",
            metadata={"reason": "retention_requirement_failed"},
            revocation_reason="retention_requirement_failed",
            points_delta=-250,
            created_at=created_at,
        )
    )

    assert result.reversed_event_id == reversed_event_id
    assert repository.last_call is not None
    assert repository.last_call[0] == "reverse_event"
    assert repository.last_call[1]["points_delta"] == -250
    assert repository.last_call[1]["revocation_reason"] == "retention_requirement_failed"
    assert repository.last_call[1]["created_at"] == created_at


def test_reward_progression_service_complete_objective_rejects_non_positive_increment() -> None:
    service = RewardProgressionService(StubRewardProgressionRepository())

    with pytest.raises(ValueError):
        service.complete_objective(
            ObjectiveCompletionCommand(
                account_id=uuid4(),
                objective_definition_id=uuid4(),
                increment_by=0,
            )
        )


def test_reward_progression_service_complete_objective_returns_repository_record() -> None:
    account_id = uuid4()
    objective_definition_id = uuid4()
    progress_at = datetime(2026, 4, 16, 18, 3, tzinfo=timezone.utc)
    repository = StubRewardProgressionRepository(
        objective_result=ObjectiveProgressUpdateRecord(
            account_id=account_id,
            objective_definition_id=objective_definition_id,
            objective_code="launch_zardbot",
            required_count=3,
            current_count=0,
            completed_count=1,
            repeat_iteration=2,
            status="in_progress",
            last_completed_at=progress_at,
            last_progress_at=progress_at,
            metadata={"recent_action": "launcher_opened"},
            completed_now=True,
        )
    )
    service = RewardProgressionService(repository)

    result = service.complete_objective(
        ObjectiveCompletionCommand(
            account_id=account_id,
            objective_definition_id=objective_definition_id,
            increment_by=2,
            metadata={"recent_action": "launcher_opened"},
            progress_at=progress_at,
        )
    )

    assert result.completed_now is True
    assert result.completed_count == 1
    assert repository.last_call is not None
    assert repository.last_call[0] == "complete_objective"
    assert repository.last_call[1]["increment_by"] == 2
    assert repository.last_call[1]["progress_at"] == progress_at


def test_reward_progression_service_complete_objective_raises_for_missing_progress_row() -> None:
    service = RewardProgressionService(StubRewardProgressionRepository(objective_result=None))

    with pytest.raises(RewardProgressionNotFoundError):
        service.complete_objective(
            ObjectiveCompletionCommand(
                account_id=uuid4(),
                objective_definition_id=uuid4(),
                increment_by=1,
            )
        )


def test_reward_progression_service_queues_notification_with_default_timestamp() -> None:
    account_id = uuid4()
    repository = StubRewardProgressionRepository(
        queue_result=RewardNotificationQueueRecord(
            notification_id=uuid4(),
            account_id=account_id,
            notification_type="objective_completion_queue",
            status="queued",
            sequence_order=2,
            queued_at=datetime(2026, 4, 16, 18, 5, tzinfo=timezone.utc),
            metadata={"surface": "objectives_page"},
        )
    )
    service = RewardProgressionService(repository)

    result = service.queue_notification(
        RewardNotificationQueueCommand(
            account_id=account_id,
            notification_type="objective_completion_queue",
            metadata={"surface": "objectives_page"},
        )
    )

    assert result.sequence_order == 2
    assert repository.last_call is not None
    assert repository.last_call[0] == "queue_notification"
    assert isinstance(repository.last_call[1]["queued_at"], datetime)


def test_reward_progression_service_queue_notification_raises_for_missing_account() -> None:
    service = RewardProgressionService(StubRewardProgressionRepository(queue_result=None))

    with pytest.raises(RewardProgressionNotFoundError):
        service.queue_notification(
            RewardNotificationQueueCommand(
                account_id=uuid4(),
                notification_type="objective_completion_queue",
            )
        )
