from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.reward_summary_repository import RewardSummaryRepository
from app.schemas.reward_summary import (
    RewardSummaryBadge,
    RewardSummaryNextMilestone,
    RewardSummaryPerk,
    RewardSummaryResponse,
)


class RewardSummaryNotFoundError(Exception):
    """Raised when no rewards summary exists for the requested account."""


class RewardSummaryService:
    def __init__(self, repository: RewardSummaryRepository) -> None:
        self._repository = repository

    def get_summary(self, account_id: UUID) -> RewardSummaryResponse:
        summary = self._repository.get_account_summary(account_id)
        if summary is None:
            raise RewardSummaryNotFoundError(f"No rewards summary exists for account {account_id}")

        next_milestone = None
        if summary.next_milestone is not None:
            next_milestone = RewardSummaryNextMilestone(
                milestone_points=summary.next_milestone.milestone_points,
                points_remaining=max(
                    summary.next_milestone.milestone_points - summary.current_points,
                    0,
                ),
                tier_code=summary.next_milestone.tier_code,
                is_tier_boundary=summary.next_milestone.is_tier_boundary,
            )

        return RewardSummaryResponse(
            account_id=summary.account_id,
            current_points=summary.current_points,
            current_tier=summary.current_tier,
            current_tier_progress_points=summary.current_tier_progress_points,
            next_milestone=next_milestone,
            active_perks=[
                RewardSummaryPerk(
                    reward_code=perk.reward_code,
                    reward_type=perk.reward_type,
                    display_name=perk.display_name,
                    description=perk.description,
                    granted_at=perk.granted_at,
                )
                for perk in summary.active_perks
            ],
            earned_badges=[
                RewardSummaryBadge(
                    badge_code=badge.badge_code,
                    display_name=badge.display_name,
                    description=badge.description,
                    icon_ref=badge.icon_ref,
                    earned_at=badge.earned_at,
                )
                for badge in summary.earned_badges
            ],
        )


def build_reward_summary_service(db: Session) -> RewardSummaryService:
    return RewardSummaryService(RewardSummaryRepository(db))
