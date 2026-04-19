from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_reward_objective_service
from app.main import app
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)
from app.services.reward_objective_service import RewardObjectivesNotFoundError


class StubRewardObjectiveService:
    def __init__(self, response: RewardObjectivesResponse | None) -> None:
        self._response = response

    def get_objectives(self, account_id):  # noqa: ANN001
        if self._response is None:
            raise RewardObjectivesNotFoundError(f"missing {account_id}")
        return self._response


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context
        self.received_tokens: list[str | None] = []

    def get_authenticated_session_context(
        self,
        session_token: str | None,
    ) -> AuthenticatedSessionContext | None:
        self.received_tokens.append(session_token)
        return self._context

    @staticmethod
    def ensure_account_status_allows_authenticated_access(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context

    @staticmethod
    def ensure_email_verified(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        if context.status == "pending_verification" or context.email_verified_at is None:
            raise EmailVerificationRequiredError("Email verification is required.")
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context


def _build_context(
    *,
    status: str = "active",
    email_verified_at: datetime | None = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
) -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="rewards-user",
        email="rewards-user@example.com",
        status=status,
        role="user",
        email_verified_at=email_verified_at,
        session_created_at=now - timedelta(hours=1),
        session_expires_at=now + timedelta(hours=1),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest-client",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


client = TestClient(app)


def test_reward_objectives_route_is_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/me/objectives" in routes
    assert "/api/v1/rewards/{account_id}/objectives" not in routes


def test_reward_objectives_endpoint_returns_grouped_objective_payload() -> None:
    context = _build_context()
    viewed_at = datetime(2026, 4, 16, 13, 0, tzinfo=timezone.utc)
    response_model = RewardObjectivesResponse.model_validate(
        {
            "account_id": str(context.account_id),
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
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_objective_service] = (
        lambda: StubRewardObjectiveService(response_model)
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/objectives")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["rewards-token"]
    payload = response.json()
    assert payload["account_id"] == str(context.account_id)
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


def test_reward_objectives_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_objective_service] = (
        lambda: StubRewardObjectiveService(RewardObjectivesResponse(account_id=uuid4(), groups=[]))
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/objectives")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "email_verification_required",
            "message": "Email verification is required.",
            "details": {},
        }
    }


def test_reward_objectives_endpoint_returns_not_found_for_missing_account() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_objective_service] = lambda: StubRewardObjectiveService(None)

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/objectives")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "reward_objectives_not_found",
            "message": "Reward objectives not found.",
            "details": {},
        }
    }


def test_legacy_reward_objectives_account_path_is_not_registered() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_objective_service] = lambda: StubRewardObjectiveService(None)

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get(f"/api/v1/rewards/{uuid4()}/objectives")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
