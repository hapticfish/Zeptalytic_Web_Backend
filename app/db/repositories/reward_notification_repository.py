from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.accounts import Account
from app.db.models.rewards.reward_grants import RewardGrant
from app.db.models.rewards.reward_notifications import RewardNotification


@dataclass(slots=True)
class RewardNotificationObjectiveRecord:
    objective_definition_id: UUID
    objective_code: str
    title: str
    is_milestone_objective: bool


@dataclass(slots=True)
class RewardNotificationRewardRecord:
    reward_definition_id: UUID
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    granted_at: datetime


@dataclass(slots=True)
class RewardNotificationBadgeRecord:
    badge_definition_id: UUID
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None


@dataclass(slots=True)
class RewardNotificationEventRecord:
    reward_event_id: UUID
    event_type: str
    points_delta: int
    source_type: str
    source_reference: str
    created_at: datetime
    metadata: dict[str, object]


@dataclass(slots=True)
class RewardNotificationRecord:
    notification_id: UUID
    notification_type: str
    status: str
    queued_at: datetime
    seen_at: datetime | None
    dismissed_at: datetime | None
    sequence_order: int
    metadata: dict[str, object]
    objective: RewardNotificationObjectiveRecord | None
    reward: RewardNotificationRewardRecord | None
    badge: RewardNotificationBadgeRecord | None
    reward_event: RewardNotificationEventRecord | None


@dataclass(slots=True)
class RewardNotificationQueueRecord:
    account_id: UUID
    notifications: list[RewardNotificationRecord]


@dataclass(slots=True)
class RewardNotificationStateChangeRecord:
    account_id: UUID
    notification: RewardNotificationRecord
    pending_notifications_remaining: int


@dataclass(slots=True)
class RewardNotificationSkipAllRecord:
    account_id: UUID
    dismissed_notification_ids: list[UUID]
    dismissed_count: int
    skipped_at: datetime | None


class RewardNotificationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_notification_queue(self, account_id: UUID) -> RewardNotificationQueueRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        notifications = self._load_pending_notifications(account_id)
        return RewardNotificationQueueRecord(
            account_id=account_id,
            notifications=[self._to_record(notification) for notification in notifications],
        )

    def mark_notification_seen(
        self,
        account_id: UUID,
        notification_id: UUID,
        seen_at: datetime,
    ) -> RewardNotificationStateChangeRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        notification = self._db.scalar(
            self._notification_query().where(
                RewardNotification.account_id == account_id,
                RewardNotification.id == notification_id,
            )
        )
        if notification is None:
            return None

        if notification.status == "queued":
            notification.status = "seen"
            notification.seen_at = seen_at
            self._db.commit()
            self._db.refresh(notification)

        pending_notifications_remaining = len(self._load_pending_notifications(account_id))
        return RewardNotificationStateChangeRecord(
            account_id=account_id,
            notification=self._to_record(notification),
            pending_notifications_remaining=pending_notifications_remaining,
        )

    def skip_all_notifications(
        self,
        account_id: UUID,
        skipped_at: datetime,
    ) -> RewardNotificationSkipAllRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        notifications = self._load_pending_notifications(account_id)
        dismissed_notification_ids: list[UUID] = []

        for notification in notifications:
            notification.status = "dismissed"
            notification.seen_at = skipped_at
            notification.dismissed_at = skipped_at
            notification.notification_metadata = {
                **notification.notification_metadata,
                "skip_all": True,
            }
            dismissed_notification_ids.append(notification.id)

        self._db.commit()
        return RewardNotificationSkipAllRecord(
            account_id=account_id,
            dismissed_notification_ids=dismissed_notification_ids,
            dismissed_count=len(dismissed_notification_ids),
            skipped_at=skipped_at if dismissed_notification_ids else None,
        )

    def _load_pending_notifications(self, account_id: UUID) -> list[RewardNotification]:
        return self._db.scalars(
            self._notification_query()
            .where(
                RewardNotification.account_id == account_id,
                RewardNotification.status == "queued",
            )
            .order_by(RewardNotification.sequence_order.asc(), RewardNotification.queued_at.asc())
        ).all()

    @staticmethod
    def _notification_query():
        return select(RewardNotification).options(
            selectinload(RewardNotification.objective_definition),
            selectinload(RewardNotification.reward_grant).selectinload(
                RewardGrant.reward_definition
            ),
            selectinload(RewardNotification.badge_definition),
            selectinload(RewardNotification.reward_event),
        )

    @staticmethod
    def _to_record(notification: RewardNotification) -> RewardNotificationRecord:
        objective = None
        if notification.objective_definition is not None:
            objective = RewardNotificationObjectiveRecord(
                objective_definition_id=notification.objective_definition.id,
                objective_code=notification.objective_definition.objective_code,
                title=notification.objective_definition.title,
                is_milestone_objective=notification.objective_definition.is_milestone_objective,
            )

        reward = None
        if (
            notification.reward_grant is not None
            and notification.reward_grant.reward_definition is not None
        ):
            reward_definition = notification.reward_grant.reward_definition
            reward = RewardNotificationRewardRecord(
                reward_definition_id=reward_definition.id,
                reward_code=reward_definition.reward_code,
                reward_type=reward_definition.reward_type,
                display_name=reward_definition.display_name,
                description=reward_definition.description,
                granted_at=notification.reward_grant.granted_at,
            )

        badge = None
        if notification.badge_definition is not None:
            badge = RewardNotificationBadgeRecord(
                badge_definition_id=notification.badge_definition.id,
                badge_code=notification.badge_definition.badge_code,
                display_name=notification.badge_definition.display_name,
                description=notification.badge_definition.description,
                icon_ref=notification.badge_definition.icon_ref,
            )

        reward_event = None
        if notification.reward_event is not None:
            reward_event = RewardNotificationEventRecord(
                reward_event_id=notification.reward_event.id,
                event_type=notification.reward_event.event_type,
                points_delta=notification.reward_event.points_delta,
                source_type=notification.reward_event.source_type,
                source_reference=notification.reward_event.source_reference,
                created_at=notification.reward_event.created_at,
                metadata=notification.reward_event.event_metadata,
            )

        return RewardNotificationRecord(
            notification_id=notification.id,
            notification_type=notification.notification_type,
            status=notification.status,
            queued_at=notification.queued_at,
            seen_at=notification.seen_at,
            dismissed_at=notification.dismissed_at,
            sequence_order=notification.sequence_order,
            metadata=notification.notification_metadata,
            objective=objective,
            reward=reward,
            badge=badge,
            reward_event=reward_event,
        )
