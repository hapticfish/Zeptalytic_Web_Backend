from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RewardNotificationObjective(BaseModel):
    objective_definition_id: UUID
    objective_code: str
    title: str
    is_milestone_objective: bool


class RewardNotificationReward(BaseModel):
    reward_definition_id: UUID
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    granted_at: datetime


class RewardNotificationBadge(BaseModel):
    badge_definition_id: UUID
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None


class RewardNotificationEvent(BaseModel):
    reward_event_id: UUID
    event_type: str
    points_delta: int
    source_type: str
    source_reference: str
    created_at: datetime
    metadata: dict[str, object]


class RewardNotificationItem(BaseModel):
    notification_id: UUID
    notification_type: str
    status: str
    queued_at: datetime
    seen_at: datetime | None
    dismissed_at: datetime | None
    sequence_order: int
    metadata: dict[str, object]
    objective: RewardNotificationObjective | None
    reward: RewardNotificationReward | None
    badge: RewardNotificationBadge | None
    reward_event: RewardNotificationEvent | None


class RewardNotificationQueueResponse(BaseModel):
    account_id: UUID
    notifications: list[RewardNotificationItem]


class RewardNotificationStateChangeResponse(BaseModel):
    account_id: UUID
    notification: RewardNotificationItem
    pending_notifications_remaining: int


class RewardNotificationSkipAllResponse(BaseModel):
    account_id: UUID
    dismissed_notification_ids: list[UUID]
    dismissed_count: int
    skipped_at: datetime | None
