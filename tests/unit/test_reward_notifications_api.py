from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_reward_notification_service
from app.main import app
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)
from app.services.reward_notification_service import (
    RewardNotificationNotFoundError,
    RewardNotificationQueueNotFoundError,
)


class StubRewardNotificationService:
    def __init__(
        self,
        queue_response: RewardNotificationQueueResponse | None,
        seen_response: RewardNotificationStateChangeResponse | None,
        skip_all_response: RewardNotificationSkipAllResponse | None,
    ) -> None:
        self._queue_response = queue_response
        self._seen_response = seen_response
        self._skip_all_response = skip_all_response

    def get_notification_queue(self, account_id):  # noqa: ANN001
        if self._queue_response is None:
            raise RewardNotificationQueueNotFoundError(f"missing {account_id}")
        return self._queue_response

    def mark_notification_seen(self, account_id, notification_id):  # noqa: ANN001
        if self._seen_response is None:
            raise RewardNotificationNotFoundError(f"missing {account_id}:{notification_id}")
        return self._seen_response

    def skip_all_notifications(self, account_id):  # noqa: ANN001
        if self._skip_all_response is None:
            raise RewardNotificationQueueNotFoundError(f"missing {account_id}")
        return self._skip_all_response


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


def _build_queue_response(account_id):  # noqa: ANN001
    queued_at = datetime(2026, 4, 16, 15, 0, tzinfo=timezone.utc)
    created_at = datetime(2026, 4, 16, 14, 59, tzinfo=timezone.utc)
    return RewardNotificationQueueResponse.model_validate(
        {
            "account_id": str(account_id),
            "notifications": [
                {
                    "notification_id": str(uuid4()),
                    "notification_type": "objective_completion_queue",
                    "status": "queued",
                    "queued_at": queued_at,
                    "seen_at": None,
                    "dismissed_at": None,
                    "sequence_order": 1,
                    "metadata": {"entry_surface": "objectives_page"},
                    "objective": {
                        "objective_definition_id": str(uuid4()),
                        "objective_code": "complete_profile",
                        "title": "Complete Your Profile",
                        "is_milestone_objective": False,
                    },
                    "reward": {
                        "reward_definition_id": str(uuid4()),
                        "reward_code": "profile-badge",
                        "reward_type": "cosmetic",
                        "display_name": "Profile Badge",
                        "description": "Unlock the profile completion badge.",
                        "granted_at": queued_at,
                    },
                    "badge": {
                        "badge_definition_id": str(uuid4()),
                        "badge_code": "profile-complete",
                        "display_name": "Profile Complete",
                        "description": "Finished the profile setup objective.",
                        "icon_ref": "badges/profile-complete.svg",
                    },
                    "reward_event": {
                        "reward_event_id": str(uuid4()),
                        "event_type": "objective_completed",
                        "points_delta": 100,
                        "source_type": "objective",
                        "source_reference": "objective:complete_profile",
                        "created_at": created_at,
                        "metadata": {"entry_surface": "objectives_page"},
                    },
                }
            ],
        }
    )


def test_reward_notifications_routes_are_registered_on_api_prefix() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/me/notifications" in routes
    assert "/api/v1/rewards/me/notifications/{notification_id}/seen" in routes
    assert "/api/v1/rewards/me/notifications/skip-all" in routes
    assert "/api/v1/rewards/{account_id}/notifications" not in routes


def test_reward_notifications_endpoint_returns_ordered_queue_payload() -> None:
    context = _build_context()
    queue_response = _build_queue_response(context.account_id)
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=queue_response,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/notifications")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["rewards-token"]
    payload = response.json()
    assert payload["account_id"] == str(context.account_id)
    assert payload["notifications"][0]["notification_type"] == "objective_completion_queue"
    assert payload["notifications"][0]["objective"]["objective_code"] == "complete_profile"
    assert payload["notifications"][0]["reward"]["reward_code"] == "profile-badge"
    assert payload["notifications"][0]["badge"]["badge_code"] == "profile-complete"
    assert payload["notifications"][0]["reward_event"]["points_delta"] == 100


def test_reward_notifications_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = (
        lambda: StubRewardNotificationService(
            queue_response=_build_queue_response(uuid4()),
            seen_response=None,
            skip_all_response=None,
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/notifications")
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


def test_reward_notifications_endpoint_returns_not_found_for_missing_account() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get("/api/v1/rewards/me/notifications")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "reward_notification_queue_not_found",
            "message": "Reward notification queue not found.",
            "details": {},
        }
    }


def test_mark_reward_notification_seen_returns_transition_payload() -> None:
    context = _build_context()
    queue_response = _build_queue_response(context.account_id)
    notification = queue_response.notifications[0].model_copy(
        update={
            "status": "seen",
            "seen_at": datetime(2026, 4, 16, 15, 1, tzinfo=timezone.utc),
        }
    )
    seen_response = RewardNotificationStateChangeResponse(
        account_id=context.account_id,
        notification=notification,
        pending_notifications_remaining=0,
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=queue_response,
        seen_response=seen_response,
        skip_all_response=None,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.post(f"/api/v1/rewards/me/notifications/{notification.notification_id}/seen")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["notification"]["status"] == "seen"
    assert response.json()["pending_notifications_remaining"] == 0


def test_mark_reward_notification_seen_returns_not_found_for_missing_notification() -> None:
    auth_service = StubAuthService(_build_context())
    notification_id = uuid4()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.post(f"/api/v1/rewards/me/notifications/{notification_id}/seen")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "reward_notification_not_found",
            "message": "Reward notification not found.",
            "details": {},
        }
    }


def test_skip_all_reward_notifications_returns_skip_summary() -> None:
    context = _build_context()
    skipped_at = datetime(2026, 4, 16, 15, 2, tzinfo=timezone.utc)
    dismissed_notification_ids = [uuid4(), uuid4()]
    skip_response = RewardNotificationSkipAllResponse(
        account_id=context.account_id,
        dismissed_notification_ids=dismissed_notification_ids,
        dismissed_count=2,
        skipped_at=skipped_at,
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=skip_response,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.post("/api/v1/rewards/me/notifications/skip-all")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(context.account_id),
        "dismissed_notification_ids": [
            str(notification_id) for notification_id in dismissed_notification_ids
        ],
        "dismissed_count": 2,
        "skipped_at": "2026-04-16T15:02:00Z",
    }


def test_skip_all_reward_notifications_returns_not_found_for_missing_account() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.post("/api/v1/rewards/me/notifications/skip-all")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "reward_notification_queue_not_found",
            "message": "Reward notification queue not found.",
            "details": {},
        }
    }


def test_legacy_reward_notifications_account_paths_are_not_registered() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_reward_notification_service] = (
        lambda: StubRewardNotificationService(
            queue_response=None,
            seen_response=None,
            skip_all_response=None,
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "rewards-token")
        response = client.get(f"/api/v1/rewards/{uuid4()}/notifications")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
