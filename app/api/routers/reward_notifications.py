from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.repositories.reward_notification_repository import RewardNotificationRepository
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.services.reward_notification_service import (
    RewardNotificationNotFoundError,
    RewardNotificationService,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_notification_service(
    db: Session = Depends(get_db),
) -> RewardNotificationService:
    return RewardNotificationService(RewardNotificationRepository(db))


@router.get("/{account_id}/notifications", response_model=RewardNotificationQueueResponse)
def get_reward_notifications(
    account_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationQueueResponse:
    try:
        return service.get_notification_queue(account_id)
    except RewardNotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward notification queue not found.",
        ) from exc


@router.post(
    "/{account_id}/notifications/{notification_id}/seen",
    response_model=RewardNotificationStateChangeResponse,
)
def mark_reward_notification_seen(
    account_id: UUID,
    notification_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationStateChangeResponse:
    try:
        return service.mark_notification_seen(account_id, notification_id)
    except RewardNotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward notification not found.",
        ) from exc


@router.post(
    "/{account_id}/notifications/skip-all",
    response_model=RewardNotificationSkipAllResponse,
)
def skip_all_reward_notifications(
    account_id: UUID,
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationSkipAllResponse:
    try:
        return service.skip_all_notifications(account_id)
    except RewardNotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward notification queue not found.",
        ) from exc
