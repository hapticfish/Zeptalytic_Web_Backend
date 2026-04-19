from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.reward_progression_repository import (
    ObjectiveProgressUpdateRecord,
    RewardEventSourceRecord,
    RewardProgressionRepository,
    RewardNotificationQueueRecord,
)
from app.services.reward_progression_service import (
    ObjectiveCompletionCommand,
    RewardNotificationQueueCommand,
    RewardPointsAwardCommand,
    RewardProgressionService,
)


class RewardEventIngestionValidationError(Exception):
    """Raised when a trusted reward event command is incomplete."""


@dataclass(slots=True)
class RewardEventIngestionCommand:
    account_id: UUID
    event_type: str
    source_type: str
    event_id: str
    source_reference: str | None = None
    objective_definition_id: UUID | None = None
    objective_increment_by: int | None = None
    points_delta: int = 0
    notification_type: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime | None = None


@dataclass(slots=True)
class RewardEventIngestionResult:
    account_id: UUID
    event_type: str
    source_type: str
    source_reference: str
    duplicate: bool
    existing_event: RewardEventSourceRecord | None = None
    points_event_id: UUID | None = None
    objective_progress: ObjectiveProgressUpdateRecord | None = None
    notification: RewardNotificationQueueRecord | None = None


class RewardEventIngestionService:
    def __init__(
        self,
        repository: RewardProgressionRepository,
        progression_service: RewardProgressionService,
    ) -> None:
        self._repository = repository
        self._progression_service = progression_service

    def ingest_event(self, command: RewardEventIngestionCommand) -> RewardEventIngestionResult:
        normalized_reference = self._normalize_source_reference(command)
        self._validate_command(command)

        existing_event = self._repository.find_event_by_source(
            account_id=command.account_id,
            source_type=command.source_type,
            source_reference=normalized_reference,
        )
        if existing_event is not None:
            return RewardEventIngestionResult(
                account_id=command.account_id,
                event_type=command.event_type,
                source_type=command.source_type,
                source_reference=normalized_reference,
                duplicate=True,
                existing_event=existing_event,
            )

        occurred_at = command.occurred_at or datetime.now(timezone.utc)
        event_metadata = {
            **command.metadata,
            "event_id": command.event_id,
            "source_reference": normalized_reference,
        }

        objective_progress = None
        if command.objective_definition_id is not None and command.objective_increment_by is not None:
            objective_progress = self._progression_service.complete_objective(
                ObjectiveCompletionCommand(
                    account_id=command.account_id,
                    objective_definition_id=command.objective_definition_id,
                    increment_by=command.objective_increment_by,
                    metadata=event_metadata,
                    progress_at=occurred_at,
                )
            )

        points_event = None
        if command.points_delta != 0:
            points_event = self._progression_service.award_points(
                RewardPointsAwardCommand(
                    account_id=command.account_id,
                    event_type=command.event_type,
                    points_delta=command.points_delta,
                    source_type=command.source_type,
                    source_reference=normalized_reference,
                    objective_definition_id=command.objective_definition_id,
                    metadata=event_metadata,
                    created_at=occurred_at,
                )
            )

        notification = None
        if command.notification_type is not None:
            notification = self._progression_service.queue_notification(
                RewardNotificationQueueCommand(
                    account_id=command.account_id,
                    notification_type=command.notification_type,
                    objective_definition_id=command.objective_definition_id,
                    reward_event_id=None if points_event is None else points_event.event_id,
                    metadata=event_metadata,
                    queued_at=occurred_at,
                )
            )

        return RewardEventIngestionResult(
            account_id=command.account_id,
            event_type=command.event_type,
            source_type=command.source_type,
            source_reference=normalized_reference,
            duplicate=False,
            points_event_id=None if points_event is None else points_event.event_id,
            objective_progress=objective_progress,
            notification=notification,
        )

    def _normalize_source_reference(self, command: RewardEventIngestionCommand) -> str:
        if command.source_reference is not None and command.source_reference.strip():
            return command.source_reference.strip()
        return command.event_id.strip()

    def _validate_command(self, command: RewardEventIngestionCommand) -> None:
        if not command.source_type.strip():
            raise RewardEventIngestionValidationError("Trusted reward events must include a source type.")
        if not command.event_id.strip():
            raise RewardEventIngestionValidationError("Trusted reward events must include an event id.")

        has_objective_action = (
            command.objective_definition_id is not None and command.objective_increment_by is not None
        )
        has_points_action = command.points_delta != 0
        has_notification_action = command.notification_type is not None
        if not any((has_objective_action, has_points_action, has_notification_action)):
            raise RewardEventIngestionValidationError(
                "Trusted reward events must request at least one progression action."
            )

        if command.objective_definition_id is None and command.objective_increment_by is not None:
            raise RewardEventIngestionValidationError(
                "Objective progress updates require an objective definition id."
            )
        if command.objective_definition_id is not None and command.objective_increment_by is None:
            raise RewardEventIngestionValidationError(
                "Objective progress updates require an increment amount."
            )


def build_reward_event_ingestion_service(db: Session) -> RewardEventIngestionService:
    repository = RewardProgressionRepository(db)
    return RewardEventIngestionService(repository, RewardProgressionService(repository))
