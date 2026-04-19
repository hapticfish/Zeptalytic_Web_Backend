from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_reward_summary_service
from app.main import app
from app.schemas.reward_summary import (
    RewardSummaryBadge,
    RewardSummaryNextMilestone,
    RewardSummaryPerk,
    RewardSummaryResponse,
)
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)
from app.services.reward_summary_service import RewardSummaryNotFoundError
from tests.unit.assertions import assert_standard_error_response


class StubRewardSummaryService:
    def __init__(self, summary: RewardSummaryResponse | None) -> None:
        self._summary = summary

    def get_summary(self, account_id):  # noqa: ANN001
        if self._summary is None:
            raise RewardSummaryNotFoundError(f"missing {account_id}")
        return self._summary


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


def test_rewards_summary_route_is_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/me/summary" in routes
    assert "/api/v1/rewards/{account_id}/summary" not in routes


def test_rewards_summary_endpoint_returns_summary_payload_for_authenticated_account() -> None:
    context = _build_context()
    granted_at = datetime(2026, 4, 16, 12, 0, tzinfo=timezone.utc)
    earned_at = datetime(2026, 4, 16, 12, 5, tzinfo=timezone.utc)
    summary = RewardSummaryResponse(
        account_id=context.account_id,
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
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(summary)

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/summary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["rewards-token"]
    assert response.json() == {
        "account_id": str(context.account_id),
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


def test_rewards_summary_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(
        RewardSummaryResponse(
            account_id=uuid4(),
            current_points=0,
            current_tier="BRONZE",
            current_tier_progress_points=0,
            next_milestone=None,
            active_perks=[],
            earned_badges=[],
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/summary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=403,
        code="email_verification_required",
        message="Email verification is required.",
        details={},
    )


def test_rewards_summary_endpoint_returns_not_found_for_missing_account_summary() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(None)

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/summary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=404,
        code="reward_summary_not_found",
        message="Reward summary not found.",
        details={},
    )


def test_legacy_rewards_summary_account_path_is_not_registered() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_summary_service] = lambda: StubRewardSummaryService(None)

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get(f"/api/v1/rewards/{uuid4()}/summary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
