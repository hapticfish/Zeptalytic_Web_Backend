from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.db.repositories.reward_progression_repository import (
    ObjectiveProgressUpdateRecord,
    RewardEventApplicationRecord,
    RewardNotificationQueueRecord,
    RewardProgressionRepository,
)


class RewardProgressionNotFoundError(Exception):
    """Raised when a progression action references missing domain rows."""


@dataclass(slots=True)
class RewardPointsAwardCommand:
    account_id: UUID
    event_type: str
    points_delta: int
    source_type: str
    source_reference: str | None = None
    objective_definition_id: UUID | None = None
    reward_definition_id: UUID | None = None
    badge_definition_id: UUID | None = None
    status: str = "applied"
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(slots=True)
class RewardPointsReversalCommand:
    account_id: UUID
    reversed_event_id: UUID
    event_type: str
    source_type: str
    source_reference: str | None = None
    status: str = "reversed"
    metadata: dict[str, object] = field(default_factory=dict)
    revocation_reason: str | None = None
    points_delta: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ObjectiveCompletionCommand:
    account_id: UUID
    objective_definition_id: UUID
    increment_by: int = 1
    metadata: dict[str, object] = field(default_factory=dict)
    progress_at: datetime | None = None


@dataclass(slots=True)
class RewardNotificationQueueCommand:
    account_id: UUID
    notification_type: str
    metadata: dict[str, object] = field(default_factory=dict)
    status: str = "queued"
    objective_definition_id: UUID | None = None
    reward_grant_id: UUID | None = None
    badge_definition_id: UUID | None = None
    reward_event_id: UUID | None = None
    queued_at: datetime | None = None


class RewardProgressionService:
    def __init__(self, repository: RewardProgressionRepository) -> None:
        self._repository = repository

    def award_points(self, command: RewardPointsAwardCommand) -> RewardEventApplicationRecord:
        created_at = command.created_at or datetime.now(timezone.utc)
        result = self._repository.award_points(
            account_id=command.account_id,
            event_type=command.event_type,
            points_delta=command.points_delta,
            source_type=command.source_type,
            source_reference=command.source_reference,
            objective_definition_id=command.objective_definition_id,
            reward_definition_id=command.reward_definition_id,
            badge_definition_id=command.badge_definition_id,
            status=command.status,
            created_at=created_at,
            metadata=command.metadata,
        )
        if result is None:
            raise RewardProgressionNotFoundError(
                f"Unable to award points for account {command.account_id}"
            )
        return result

    def reverse_points(self, command: RewardPointsReversalCommand) -> RewardEventApplicationRecord:
        created_at = command.created_at or datetime.now(timezone.utc)
        result = self._repository.reverse_event(
            account_id=command.account_id,
            reversed_event_id=command.reversed_event_id,
            event_type=command.event_type,
            source_type=command.source_type,
            source_reference=command.source_reference,
            status=command.status,
            created_at=created_at,
            metadata=command.metadata,
            revocation_reason=command.revocation_reason,
            points_delta=command.points_delta,
        )
        if result is None:
            raise RewardProgressionNotFoundError(
                f"Unable to reverse points for account {command.account_id}"
            )
        return result

    def complete_objective(
        self,
        command: ObjectiveCompletionCommand,
    ) -> ObjectiveProgressUpdateRecord:
        if command.increment_by <= 0:
            raise ValueError("Objective progress increments must be positive.")

        progress_at = command.progress_at or datetime.now(timezone.utc)
        result = self._repository.complete_objective(
            account_id=command.account_id,
            objective_definition_id=command.objective_definition_id,
            increment_by=command.increment_by,
            progress_at=progress_at,
            metadata=command.metadata,
        )
        if result is None:
            raise RewardProgressionNotFoundError(
                f"Unable to update objective progress for account {command.account_id}"
            )
        return result

    def queue_notification(
        self,
        command: RewardNotificationQueueCommand,
    ) -> RewardNotificationQueueRecord:
        queued_at = command.queued_at or datetime.now(timezone.utc)
        result = self._repository.queue_notification(
            account_id=command.account_id,
            notification_type=command.notification_type,
            queued_at=queued_at,
            metadata=command.metadata,
            status=command.status,
            objective_definition_id=command.objective_definition_id,
            reward_grant_id=command.reward_grant_id,
            badge_definition_id=command.badge_definition_id,
            reward_event_id=command.reward_event_id,
        )
        if result is None:
            raise RewardProgressionNotFoundError(
                f"Unable to queue reward notification for account {command.account_id}"
            )
        return result
