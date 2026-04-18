from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.repositories.reward_objective_repository import RewardObjectiveRepository
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.services.reward_objective_service import (
    RewardObjectiveService,
    RewardObjectivesNotFoundError,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_objective_service(db: Session = Depends(get_db)) -> RewardObjectiveService:
    return RewardObjectiveService(RewardObjectiveRepository(db))


@router.get("/{account_id}/objectives", response_model=RewardObjectivesResponse)
def get_reward_objectives(
    account_id: UUID,
    service: RewardObjectiveService = Depends(get_reward_objective_service),
) -> RewardObjectivesResponse:
    try:
        return service.get_objectives(account_id)
    except RewardObjectivesNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward objectives not found.",
        ) from exc
