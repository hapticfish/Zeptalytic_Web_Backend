from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.reward_badge_repository import RewardBadgeGalleryRecord
from app.services.reward_badge_service import RewardBadgeService


class StubRewardBadgeRepository:
    def __init__(self, records: list[RewardBadgeGalleryRecord]) -> None:
        self._records = records
        self.received_account_ids: list = []

    def list_badges_for_account(self, account_id):  # noqa: ANN001
        self.received_account_ids.append(account_id)
        return self._records


def test_reward_badge_service_maps_earned_and_locked_badges_to_safe_dto() -> None:
    account_id = uuid4()
    earned_at = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
    repository = StubRewardBadgeRepository(
        [
            RewardBadgeGalleryRecord(
                badge_code="founder",
                display_name="Founder",
                description="Joined during the founder launch window.",
                icon_ref="badges/founder.svg",
                earned_at=earned_at,
            ),
            RewardBadgeGalleryRecord(
                badge_code="power-user",
                display_name="Power User",
                description="Complete the advanced product onboarding path.",
                icon_ref="badges/power-user.svg",
                earned_at=None,
            ),
        ]
    )

    response = RewardBadgeService(repository).get_badge_gallery(account_id)

    assert repository.received_account_ids == [account_id]
    assert response.model_dump(mode="json") == {
        "account_id": str(account_id),
        "badges": [
            {
                "badge_code": "founder",
                "display_name": "Founder",
                "description": "Joined during the founder launch window.",
                "icon_ref": "badges/founder.svg",
                "earned": True,
                "earned_at": "2026-04-18T12:00:00Z",
            },
            {
                "badge_code": "power-user",
                "display_name": "Power User",
                "description": "Complete the advanced product onboarding path.",
                "icon_ref": "badges/power-user.svg",
                "earned": False,
                "earned_at": None,
            },
        ],
    }


def test_reward_badge_service_returns_empty_gallery_when_no_badges_exist() -> None:
    account_id = uuid4()
    repository = StubRewardBadgeRepository([])

    response = RewardBadgeService(repository).get_badge_gallery(account_id)

    assert repository.received_account_ids == [account_id]
    assert response.model_dump(mode="json") == {
        "account_id": str(account_id),
        "badges": [],
    }
