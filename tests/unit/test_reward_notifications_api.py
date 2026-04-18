from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routers.reward_notifications import get_reward_notification_service
from app.main import app
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.services.reward_notification_service import RewardNotificationNotFoundError


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
            raise RewardNotificationNotFoundError(f"missing {account_id}")
        return self._queue_response

    def mark_notification_seen(self, account_id, notification_id):  # noqa: ANN001
        if self._seen_response is None:
            raise RewardNotificationNotFoundError(f"missing {account_id}:{notification_id}")
        return self._seen_response

    def skip_all_notifications(self, account_id):  # noqa: ANN001
        if self._skip_all_response is None:
            raise RewardNotificationNotFoundError(f"missing {account_id}")
        return self._skip_all_response


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
    assert "/api/v1/rewards/{account_id}/notifications" in routes
    assert "/api/v1/rewards/{account_id}/notifications/{notification_id}/seen" in routes
    assert "/api/v1/rewards/{account_id}/notifications/skip-all" in routes


def test_reward_notifications_endpoint_returns_ordered_queue_payload() -> None:
    account_id = uuid4()
    queue_response = _build_queue_response(account_id)
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=queue_response,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/notifications")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_id"] == str(account_id)
    assert payload["notifications"][0]["notification_type"] == "objective_completion_queue"
    assert payload["notifications"][0]["objective"]["objective_code"] == "complete_profile"
    assert payload["notifications"][0]["reward"]["reward_code"] == "profile-badge"
    assert payload["notifications"][0]["badge"]["badge_code"] == "profile-complete"
    assert payload["notifications"][0]["reward_event"]["points_delta"] == 100


def test_reward_notifications_endpoint_returns_not_found_for_missing_account() -> None:
    account_id = uuid4()
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        response = client.get(f"/api/v1/rewards/{account_id}/notifications")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Reward notification queue not found."}


def test_mark_reward_notification_seen_returns_transition_payload() -> None:
    account_id = uuid4()
    queue_response = _build_queue_response(account_id)
    notification = queue_response.notifications[0].model_copy(
        update={
            "status": "seen",
            "seen_at": datetime(2026, 4, 16, 15, 1, tzinfo=timezone.utc),
        }
    )
    seen_response = RewardNotificationStateChangeResponse(
        account_id=account_id,
        notification=notification,
        pending_notifications_remaining=0,
    )
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=queue_response,
        seen_response=seen_response,
        skip_all_response=None,
    )

    try:
        response = client.post(
            f"/api/v1/rewards/{account_id}/notifications/{notification.notification_id}/seen"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["notification"]["status"] == "seen"
    assert response.json()["pending_notifications_remaining"] == 0


def test_mark_reward_notification_seen_returns_not_found_for_missing_notification() -> None:
    account_id = uuid4()
    notification_id = uuid4()
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        response = client.post(
            f"/api/v1/rewards/{account_id}/notifications/{notification_id}/seen"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Reward notification not found."}


def test_skip_all_reward_notifications_returns_skip_summary() -> None:
    account_id = uuid4()
    skipped_at = datetime(2026, 4, 16, 15, 2, tzinfo=timezone.utc)
    dismissed_notification_ids = [uuid4(), uuid4()]
    skip_response = RewardNotificationSkipAllResponse(
        account_id=account_id,
        dismissed_notification_ids=dismissed_notification_ids,
        dismissed_count=2,
        skipped_at=skipped_at,
    )
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=skip_response,
    )

    try:
        response = client.post(f"/api/v1/rewards/{account_id}/notifications/skip-all")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(account_id),
        "dismissed_notification_ids": [
            str(notification_id) for notification_id in dismissed_notification_ids
        ],
        "dismissed_count": 2,
        "skipped_at": "2026-04-16T15:02:00Z",
    }


def test_skip_all_reward_notifications_returns_not_found_for_missing_account() -> None:
    account_id = uuid4()
    app.dependency_overrides[get_reward_notification_service] = lambda: StubRewardNotificationService(
        queue_response=None,
        seen_response=None,
        skip_all_response=None,
    )

    try:
        response = client.post(f"/api/v1/rewards/{account_id}/notifications/skip-all")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Reward notification queue not found."}
