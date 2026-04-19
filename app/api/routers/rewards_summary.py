from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_reward_summary_service,
    require_normal_authenticated_session_context,
)
from app.schemas.reward_summary import RewardSummaryResponse
from app.services import AuthenticatedSessionContext, RewardSummaryService

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("/me/summary", response_model=RewardSummaryResponse)
def get_my_reward_summary(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardSummaryService = Depends(get_reward_summary_service),
) -> RewardSummaryResponse:
    return service.get_summary(context.account_id)
