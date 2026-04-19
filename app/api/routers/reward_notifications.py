from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.services import RewardNotificationService, build_reward_notification_service

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_notification_service(
    db: Session = Depends(get_db),
) -> RewardNotificationService:
    return build_reward_notification_service(db)


@router.get("/{account_id}/notifications", response_model=RewardNotificationQueueResponse)
def get_reward_notifications(
    account_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationQueueResponse:
    return service.get_notification_queue(account_id)


@router.post(
    "/{account_id}/notifications/{notification_id}/seen",
    response_model=RewardNotificationStateChangeResponse,
)
def mark_reward_notification_seen(
    account_id: UUID,
    notification_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationStateChangeResponse:
    return service.mark_notification_seen(account_id, notification_id)


@router.post(
    "/{account_id}/notifications/skip-all",
    response_model=RewardNotificationSkipAllResponse,
)
def skip_all_reward_notifications(
    account_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationSkipAllResponse:
    return service.skip_all_notifications(account_id)
