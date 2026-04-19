from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.repositories.reward_progression_repository import (
    ObjectiveProgressUpdateRecord,
    RewardAccountSnapshotRecord,
    RewardEventApplicationRecord,
    RewardEventSourceRecord,
    RewardNotificationQueueRecord,
)
from app.services.reward_event_ingestion_service import (
    RewardEventIngestionCommand,
    RewardEventIngestionService,
    RewardEventIngestionValidationError,
)


class StubRewardProgressionRepository:
    def __init__(self, existing_event: RewardEventSourceRecord | None = None) -> None:
        self.existing_event = existing_event
        self.find_calls: list[dict[str, object]] = []

    def find_event_by_source(self, **kwargs):  # noqa: ANN003
        self.find_calls.append(kwargs)
        return self.existing_event


class StubRewardProgressionService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def complete_objective(self, command):  # noqa: ANN001
        self.calls.append(("complete_objective", asdict(command)))
        return ObjectiveProgressUpdateRecord(
            account_id=command.account_id,
            objective_definition_id=command.objective_definition_id,
            objective_code="launch_zardbot",
            required_count=3,
            current_count=0,
            completed_count=1,
            repeat_iteration=None,
            status="completed",
            last_completed_at=command.progress_at,
            last_progress_at=command.progress_at,
            metadata=command.metadata,
            completed_now=True,
        )

    def award_points(self, command):  # noqa: ANN001
        self.calls.append(("award_points", asdict(command)))
        return RewardEventApplicationRecord(
            event_id=uuid4(),
            account_id=command.account_id,
            event_type=command.event_type,
            points_delta=command.points_delta,
            is_reversal=False,
            reversed_event_id=None,
            status=command.status,
            source_type=command.source_type,
            source_reference=command.source_reference,
            created_at=command.created_at,
            metadata=command.metadata,
            reward_account=RewardAccountSnapshotRecord(
                account_id=command.account_id,
                current_points=250,
                current_tier="BRONZE",
                current_tier_progress_points=250,
                next_milestone_points=300,
                last_recomputed_at=command.created_at,
            ),
            revoked_reward_grant_ids=[],
            revoked_badge_ids=[],
        )

    def queue_notification(self, command):  # noqa: ANN001
        self.calls.append(("queue_notification", asdict(command)))
        return RewardNotificationQueueRecord(
            notification_id=uuid4(),
            account_id=command.account_id,
            notification_type=command.notification_type,
            status=command.status,
            sequence_order=1,
            queued_at=command.queued_at,
            metadata=command.metadata,
        )


def test_reward_event_ingestion_service_orchestrates_progression_actions() -> None:
    account_id = uuid4()
    objective_definition_id = uuid4()
    occurred_at = datetime(2026, 4, 19, 7, 0, tzinfo=timezone.utc)
    repository = StubRewardProgressionRepository()
    progression_service = StubRewardProgressionService()
    service = RewardEventIngestionService(repository, progression_service)

    result = service.ingest_event(
        RewardEventIngestionCommand(
            account_id=account_id,
            event_type="product_usage_confirmed",
            source_type="product_event",
            event_id="evt_zardbot_001",
            source_reference="zardbot/session/001",
            objective_definition_id=objective_definition_id,
            objective_increment_by=1,
            points_delta=250,
            notification_type="objective_completion_queue",
            metadata={"product_code": "zardbot"},
            occurred_at=occurred_at,
        )
    )

    assert repository.find_calls == [
        {
            "account_id": account_id,
            "source_type": "product_event",
            "source_reference": "zardbot/session/001",
        }
    ]
    assert [name for name, _ in progression_service.calls] == [
        "complete_objective",
        "award_points",
        "queue_notification",
    ]
    assert result.duplicate is False
    assert result.objective_progress is not None
    assert result.points_event_id is not None
    assert result.notification is not None
    for _, call in progression_service.calls:
        assert call["metadata"]["event_id"] == "evt_zardbot_001"
        assert call["metadata"]["source_reference"] == "zardbot/session/001"


def test_reward_event_ingestion_service_short_circuits_duplicate_source_reference() -> None:
    account_id = uuid4()
    existing_event = RewardEventSourceRecord(
        event_id=uuid4(),
        account_id=account_id,
        source_type="worker",
        source_reference="job/reward-sync/42",
        event_type="milestone_recomputed",
        created_at=datetime(2026, 4, 19, 7, 5, tzinfo=timezone.utc),
    )
    repository = StubRewardProgressionRepository(existing_event=existing_event)
    progression_service = StubRewardProgressionService()
    service = RewardEventIngestionService(repository, progression_service)

    result = service.ingest_event(
        RewardEventIngestionCommand(
            account_id=account_id,
            event_type="milestone_recomputed",
            source_type="worker",
            event_id="evt_reward_sync_42",
            source_reference="job/reward-sync/42",
            points_delta=100,
        )
    )

    assert result.duplicate is True
    assert result.existing_event == existing_event
    assert progression_service.calls == []


def test_reward_event_ingestion_service_requires_trusted_event_id() -> None:
    service = RewardEventIngestionService(
        StubRewardProgressionRepository(),
        StubRewardProgressionService(),
    )

    with pytest.raises(RewardEventIngestionValidationError):
        service.ingest_event(
            RewardEventIngestionCommand(
                account_id=uuid4(),
                event_type="product_usage_confirmed",
                source_type="product_event",
                event_id=" ",
                points_delta=25,
            )
        )


def test_reward_event_ingestion_service_requires_at_least_one_progression_action() -> None:
    service = RewardEventIngestionService(
        StubRewardProgressionRepository(),
        StubRewardProgressionService(),
    )

    with pytest.raises(RewardEventIngestionValidationError):
        service.ingest_event(
            RewardEventIngestionCommand(
                account_id=uuid4(),
                event_type="product_usage_confirmed",
                source_type="product_event",
                event_id="evt_zardbot_002",
            )
        )
