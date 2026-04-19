from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.reward_badge_repository import RewardBadgeRepository
from app.schemas.reward_badges import RewardBadgeGalleryItem, RewardBadgeGalleryResponse


class RewardBadgeService:
    def __init__(self, repository: RewardBadgeRepository) -> None:
        self._repository = repository

    def get_badge_gallery(self, account_id: UUID) -> RewardBadgeGalleryResponse:
        badges = self._repository.list_badges_for_account(account_id)
        return RewardBadgeGalleryResponse(
            account_id=account_id,
            badges=[
                RewardBadgeGalleryItem(
                    badge_code=badge.badge_code,
                    display_name=badge.display_name,
                    description=badge.description,
                    icon_ref=badge.icon_ref,
                    earned=badge.earned_at is not None,
                    earned_at=badge.earned_at,
                )
                for badge in badges
            ],
        )


def build_reward_badge_service(db: Session) -> RewardBadgeService:
    return RewardBadgeService(RewardBadgeRepository(db))
