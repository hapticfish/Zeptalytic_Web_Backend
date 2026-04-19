from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_reward_objective_service,
    require_normal_authenticated_session_context,
)
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.services import AuthenticatedSessionContext, RewardObjectiveService

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("/me/objectives", response_model=RewardObjectivesResponse)
def get_my_reward_objectives(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: RewardObjectiveService = Depends(get_reward_objective_service),
) -> RewardObjectivesResponse:
    return service.get_objectives(context.account_id)
