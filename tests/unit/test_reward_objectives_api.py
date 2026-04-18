from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routers.reward_objectives import get_reward_objective_service
from app.main import app
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.services.reward_objective_service import RewardObjectivesNotFoundError


class StubRewardObjectiveService:
    def __init__(self, response: RewardObjectivesResponse | None) -> None:
        self._response = response

    def get_objectives(self, account_id):  # noqa: ANN001
        if self._response is None:
            raise RewardObjectivesNotFoundError(f"missing {account_id}")
        return self._response


client = TestClient(app)


def test_reward_objectives_route_is_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/{account_id}/objectives" in routes


def test_reward_objectives_endpoint_returns_grouped_objective_payload() -> None:
    account_id = uuid4()
    viewed_at = datetime(2026, 4, 16, 13, 0, tzinfo=timezone.utc)
    response_model = RewardObjectivesResponse.model_validate(
        {
            "account_id": str(account_id),
            "groups": [
                {
                    "group_code": "milestones",
                    "objectives": [
                        {
                            "objective_definition_id": str(uuid4()),
                            "objective_code": "milestone_0100",
                            "title": "Reach 100 Points",
                            "description": "Cross the first milestone on the rewards bar.",
                            "scope_type": "global",
                            "product_code": None,
                            "objective_type": "milestone",
                            "is_repeatable": False,
                            "repeat_group_key": None,
                            "tier_gate": None,
                            "subscription_gate_product_code": None,
                            "subscription_gate_plan_code": None,
                            "is_milestone_objective": True,
                            "sort_group": "milestones",
                            "sort_order": 1,
                            "metadata": {
                                "milestone_points": 100,
                                "tier_code": "BRONZE",
                                "is_tier_boundary": False,
                            },
                            "progress": {
                                "current_count": 1,
                                "completed_count": 1,
                                "required_count": 1,
                                "status": "completed",
                                "repeat_iteration": None,
                                "last_completed_at": viewed_at,
                                "last_progress_at": viewed_at,
                                "metadata": {"surface": "progress_bar"},
                            },
                            "rewards": [
                                {
                                    "reward_code": "milestone-100-points",
                                    "reward_type": "milestone_reward",
                                    "display_name": "100 Point Milestone",
                                    "description": "Unlock the 100-point milestone reward.",
                                    "grant_order": 1,
                                }
                            ],
                            "linked_milestone": {
                                "milestone_points": 100,
                                "tier_code": "BRONZE",
                                "is_tier_boundary": False,
                            },
                        }
                    ],
                },
                {
                    "group_code": "product",
                    "objectives": [
                        {
                            "objective_definition_id": str(uuid4()),
                            "objective_code": "zardbot_launch_three",
                            "title": "Launch ZardBot Three Times",
                            "description": "Track product usage toward the next perk.",
                            "scope_type": "product",
                            "product_code": "zardbot",
                            "objective_type": "usage",
                            "is_repeatable": True,
                            "repeat_group_key": "zardbot_launches",
                            "tier_gate": "SILVER",
                            "subscription_gate_product_code": "zardbot",
                            "subscription_gate_plan_code": "pro_monthly",
                            "is_milestone_objective": False,
                            "sort_group": "product",
                            "sort_order": 900,
                            "metadata": {"surface": "objectives_page"},
                            "progress": {
                                "current_count": 2,
                                "completed_count": 0,
                                "required_count": 3,
                                "status": "in_progress",
                                "repeat_iteration": 1,
                                "last_completed_at": None,
                                "last_progress_at": viewed_at,
                                "metadata": {"recent_action": "launcher_opened"},
                            },
                            "rewards": [
                                {
                                    "reward_code": "silver-chat-badge",
                                    "reward_type": "cosmetic",
                                    "display_name": "Silver Chat Badge",
                                    "description": "Unlock silver-tier chat styling.",
                                    "grant_order": 1,
                                }
                            ],
                            "linked_milestone": None,
                        }
                    ],
                },
            ],
        }
    )
    app.dependency_overrides[get_reward_objective_service] = (
        lambda: StubRewardObjectiveService(response_model)
    )

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/objectives")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_id"] == str(account_id)
    assert [group["group_code"] for group in payload["groups"]] == ["milestones", "product"]
    assert payload["groups"][0]["objectives"][0]["linked_milestone"] == {
        "milestone_points": 100,
        "tier_code": "BRONZE",
        "is_tier_boundary": False,
    }
    assert payload["groups"][1]["objectives"][0]["progress"] == {
        "current_count": 2,
        "completed_count": 0,
        "required_count": 3,
        "status": "in_progress",
        "repeat_iteration": 1,
        "last_completed_at": None,
        "last_progress_at": "2026-04-16T13:00:00Z",
        "metadata": {"recent_action": "launcher_opened"},
    }


def test_reward_objectives_endpoint_returns_not_found_for_missing_account() -> None:
    account_id = uuid4()
    app.dependency_overrides[get_reward_objective_service] = lambda: StubRewardObjectiveService(None)

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/objectives")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Reward objectives not found."}
