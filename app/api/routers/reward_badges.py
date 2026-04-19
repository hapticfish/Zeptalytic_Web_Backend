from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_reward_badge_service,
    require_normal_authenticated_session_context,
)
from app.schemas.reward_badges import RewardBadgeGalleryResponse
from app.services import AuthenticatedSessionContext, RewardBadgeService

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("/me/badges", response_model=RewardBadgeGalleryResponse)
def get_my_reward_badges(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardBadgeService = Depends(get_reward_badge_service),
) -> RewardBadgeGalleryResponse:
    return service.get_badge_gallery(context.account_id)
