from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.repositories.reward_summary_repository import RewardSummaryRepository
from app.schemas.reward_summary import RewardSummaryResponse
from app.services.reward_summary_service import (
    RewardSummaryNotFoundError,
    RewardSummaryService,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_summary_service(db: Session = Depends(get_db)) -> RewardSummaryService:
    return RewardSummaryService(RewardSummaryRepository(db))


@router.get("/{account_id}/summary", response_model=RewardSummaryResponse)
def get_reward_summary(
    account_id: UUID,
    service: RewardSummaryService = Depends(get_reward_summary_service),
) -> RewardSummaryResponse:
    try:
        return service.get_summary(account_id)
    except RewardSummaryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward summary not found.",
        ) from exc
