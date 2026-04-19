from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.services import RewardObjectiveService, build_reward_objective_service

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_objective_service(db: Session = Depends(get_db)) -> RewardObjectiveService:
    return build_reward_objective_service(db)


@router.get("/{account_id}/objectives", response_model=RewardObjectivesResponse)
def get_reward_objectives(
    account_id: UUID,
    service: RewardObjectiveService = Depends(get_reward_objective_service),
) -> RewardObjectivesResponse:
    return service.get_objectives(account_id)
