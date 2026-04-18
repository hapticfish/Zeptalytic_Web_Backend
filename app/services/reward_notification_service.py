from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.db.repositories.reward_notification_repository import RewardNotificationRepository
from app.schemas.reward_notifications import (
    RewardNotificationBadge,
    RewardNotificationEvent,
    RewardNotificationItem,
    RewardNotificationObjective,
    RewardNotificationQueueResponse,
    RewardNotificationReward,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)


class RewardNotificationNotFoundError(Exception):
    """Raised when the requested account or notification does not exist."""


class RewardNotificationService:
    def __init__(self, repository: RewardNotificationRepository) -> None:
        self._repository = repository

    def get_notification_queue(self, account_id: UUID) -> RewardNotificationQueueResponse:
        queue = self._repository.get_notification_queue(account_id)
        if queue is None:
            raise RewardNotificationNotFoundError(f"No account exists for {account_id}")

        return RewardNotificationQueueResponse(
            account_id=queue.account_id,
            notifications=[self._to_schema(notification) for notification in queue.notifications],
        )

    def mark_notification_seen(
        self,
        account_id: UUID,
        notification_id: UUID,
    ) -> RewardNotificationStateChangeResponse:
        state_change = self._repository.mark_notification_seen(
            account_id=account_id,
            notification_id=notification_id,
            seen_at=datetime.now(timezone.utc),
        )
        if state_change is None:
            raise RewardNotificationNotFoundError(
                f"No queued reward notification exists for account {account_id}"
            )

        return RewardNotificationStateChangeResponse(
            account_id=state_change.account_id,
            notification=self._to_schema(state_change.notification),
            pending_notifications_remaining=state_change.pending_notifications_remaining,
        )

    def skip_all_notifications(self, account_id: UUID) -> RewardNotificationSkipAllResponse:
        skip_result = self._repository.skip_all_notifications(
            account_id=account_id,
            skipped_at=datetime.now(timezone.utc),
        )
        if skip_result is None:
            raise RewardNotificationNotFoundError(f"No account exists for {account_id}")

        return RewardNotificationSkipAllResponse(
            account_id=skip_result.account_id,
            dismissed_notification_ids=skip_result.dismissed_notification_ids,
            dismissed_count=skip_result.dismissed_count,
            skipped_at=skip_result.skipped_at,
        )

    @staticmethod
    def _to_schema(record):  # noqa: ANN001
        return RewardNotificationItem(
            notification_id=record.notification_id,
            notification_type=record.notification_type,
            status=record.status,
            queued_at=record.queued_at,
            seen_at=record.seen_at,
            dismissed_at=record.dismissed_at,
            sequence_order=record.sequence_order,
            metadata=record.metadata,
            objective=(
                RewardNotificationObjective(
                    objective_definition_id=record.objective.objective_definition_id,
                    objective_code=record.objective.objective_code,
                    title=record.objective.title,
                    is_milestone_objective=record.objective.is_milestone_objective,
                )
                if record.objective is not None
                else None
            ),
            reward=(
                RewardNotificationReward(
                    reward_definition_id=record.reward.reward_definition_id,
                    reward_code=record.reward.reward_code,
                    reward_type=record.reward.reward_type,
                    display_name=record.reward.display_name,
                    description=record.reward.description,
                    granted_at=record.reward.granted_at,
                )
                if record.reward is not None
                else None
            ),
            badge=(
                RewardNotificationBadge(
                    badge_definition_id=record.badge.badge_definition_id,
                    badge_code=record.badge.badge_code,
                    display_name=record.badge.display_name,
                    description=record.badge.description,
                    icon_ref=record.badge.icon_ref,
                )
                if record.badge is not None
                else None
            ),
            reward_event=(
                RewardNotificationEvent(
                    reward_event_id=record.reward_event.reward_event_id,
                    event_type=record.reward_event.event_type,
                    points_delta=record.reward_event.points_delta,
                    source_type=record.reward_event.source_type,
                    source_reference=record.reward_event.source_reference,
                    created_at=record.reward_event.created_at,
                    metadata=record.reward_event.metadata,
                )
                if record.reward_event is not None
                else None
            ),
        )
