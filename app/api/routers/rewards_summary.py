from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reward_summary import RewardSummaryResponse
from app.services import RewardSummaryService, build_reward_summary_service

router = APIRouter(prefix="/rewards", tags=["rewards"])


def get_reward_summary_service(db: Session = Depends(get_db)) -> RewardSummaryService:
    return build_reward_summary_service(db)


@router.get("/{account_id}/summary", response_model=RewardSummaryResponse)
def get_reward_summary(
    account_id: UUID,
    service: RewardSummaryService = Depends(get_reward_summary_service),
) -> RewardSummaryResponse:
    return service.get_summary(account_id)
