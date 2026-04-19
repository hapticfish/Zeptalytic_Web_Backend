from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_reward_notification_service,
    require_normal_authenticated_session_context,
)
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.services import AuthenticatedSessionContext, RewardNotificationService

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("/me/notifications", response_model=RewardNotificationQueueResponse)
def get_my_reward_notifications(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationQueueResponse:
    return service.get_notification_queue(context.account_id)


@router.post(
    "/me/notifications/{notification_id}/seen",
    response_model=RewardNotificationStateChangeResponse,
)
def mark_my_reward_notification_seen(
    notification_id: UUID,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationStateChangeResponse:
    return service.mark_notification_seen(context.account_id, notification_id)


@router.post(
    "/me/notifications/skip-all",
    response_model=RewardNotificationSkipAllResponse,
)
def skip_all_my_reward_notifications(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardNotificationService = Depends(get_reward_notification_service),
) -> RewardNotificationSkipAllResponse:
    return service.skip_all_notifications(context.account_id)
