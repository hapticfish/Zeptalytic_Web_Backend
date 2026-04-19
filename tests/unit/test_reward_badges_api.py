from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_reward_badge_service
from app.main import app
from app.schemas.reward_badges import RewardBadgeGalleryItem, RewardBadgeGalleryResponse
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)
from tests.unit.assertions import assert_standard_error_response


class StubRewardBadgeService:
    def __init__(self, response_model: RewardBadgeGalleryResponse) -> None:
        self._response_model = response_model

    def get_badge_gallery(self, account_id):  # noqa: ANN001
        return self._response_model.model_copy(update={"account_id": account_id})


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
        username="reward-badge-user",
        email="reward-badge-user@example.com",
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


def test_reward_badges_route_is_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/me/badges" in routes


def test_reward_badges_endpoint_returns_badge_gallery_for_authenticated_account() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    response_model = RewardBadgeGalleryResponse(
        account_id=context.account_id,
        badges=[
            RewardBadgeGalleryItem(
                badge_code="founder",
                display_name="Founder",
                description="Joined during the founder launch window.",
                icon_ref="badges/founder.svg",
                earned=True,
                earned_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
            ),
            RewardBadgeGalleryItem(
                badge_code="power-user",
                display_name="Power User",
                description="Complete the advanced product onboarding path.",
                icon_ref="badges/power-user.svg",
                earned=False,
                earned_at=None,
            ),
        ],
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_badge_service] = lambda: StubRewardBadgeService(
        response_model
    )

    try:
        client.cookies.set("zeptalytic_session", "reward-badges-token")
        response = client.get("/api/v1/rewards/me/badges")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["reward-badges-token"]
    assert response.json() == {
        "account_id": str(context.account_id),
        "badges": [
            {
                "badge_code": "founder",
                "display_name": "Founder",
                "description": "Joined during the founder launch window.",
                "icon_ref": "badges/founder.svg",
                "earned": True,
                "earned_at": "2026-04-18T13:00:00Z",
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


def test_reward_badges_endpoint_returns_empty_badge_gallery() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_badge_service] = lambda: StubRewardBadgeService(
        RewardBadgeGalleryResponse(account_id=context.account_id, badges=[])
    )

    try:
        client.cookies.set("zeptalytic_session", "reward-badges-token")
        response = client.get("/api/v1/rewards/me/badges")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(context.account_id),
        "badges": [],
    }


def test_reward_badges_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_badge_service] = lambda: StubRewardBadgeService(
        RewardBadgeGalleryResponse(account_id=uuid4(), badges=[])
    )

    try:
        client.cookies.set("zeptalytic_session", "reward-badges-token")
        response = client.get("/api/v1/rewards/me/badges")
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
