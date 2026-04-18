from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routers.rewards_summary import get_reward_summary_service
from app.main import app
from app.schemas.reward_summary import (
    RewardSummaryBadge,
    RewardSummaryNextMilestone,
    RewardSummaryPerk,
    RewardSummaryResponse,
)
from app.services.reward_summary_service import RewardSummaryNotFoundError


class StubRewardSummaryService:
    def __init__(self, summary: RewardSummaryResponse | None) -> None:
        self._summary = summary

    def get_summary(self, account_id):  # noqa: ANN001
        if self._summary is None:
            raise RewardSummaryNotFoundError(f"missing {account_id}")
        return self._summary


client = TestClient(app)


def test_rewards_summary_route_is_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/{account_id}/summary" in routes


def test_rewards_summary_endpoint_returns_summary_payload() -> None:
    account_id = uuid4()
    granted_at = datetime(2026, 4, 16, 12, 0, tzinfo=timezone.utc)
    earned_at = datetime(2026, 4, 16, 12, 5, tzinfo=timezone.utc)
    summary = RewardSummaryResponse(
        account_id=account_id,
        current_points=1350,
        current_tier="SILVER",
        current_tier_progress_points=350,
        next_milestone=RewardSummaryNextMilestone(
            milestone_points=1400,
            points_remaining=50,
            tier_code="SILVER",
            is_tier_boundary=False,
        ),
        active_perks=[
            RewardSummaryPerk(
                reward_code="silver-chat-badge",
                reward_type="cosmetic",
                display_name="Silver Chat Badge",
                description="Unlocked silver-tier chat styling.",
                granted_at=granted_at,
            )
        ],
        earned_badges=[
            RewardSummaryBadge(
                badge_code="silver-tier",
                display_name="Silver Tier",
                description="Reached the silver tier band.",
                icon_ref="badges/silver-tier.svg",
                earned_at=earned_at,
            )
        ],
    )
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(summary)

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(account_id),
        "current_points": 1350,
        "current_tier": "SILVER",
        "current_tier_progress_points": 350,
        "current_tier_band_max_points": 1000,
        "next_milestone": {
            "milestone_points": 1400,
            "points_remaining": 50,
            "tier_code": "SILVER",
            "is_tier_boundary": False,
        },
        "active_perks": [
            {
                "reward_code": "silver-chat-badge",
                "reward_type": "cosmetic",
                "display_name": "Silver Chat Badge",
                "description": "Unlocked silver-tier chat styling.",
                "granted_at": "2026-04-16T12:00:00Z",
            }
        ],
        "earned_badges": [
            {
                "badge_code": "silver-tier",
                "display_name": "Silver Tier",
                "description": "Reached the silver tier band.",
                "icon_ref": "badges/silver-tier.svg",
                "earned_at": "2026-04-16T12:05:00Z",
            }
        ],
    }


def test_rewards_summary_endpoint_returns_not_found_for_missing_account() -> None:
    account_id = uuid4()
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(None)

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Reward summary not found."}
