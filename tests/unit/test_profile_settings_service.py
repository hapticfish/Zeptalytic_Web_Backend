from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.services.profile_settings_service import (
    ProfileSettingsNotFoundError,
    ProfileSettingsService,
    ProfileSettingsUpdateValidationError,
)
from app.schemas.profiles import ProfileSettingsUpdateRequest


@dataclass
class StubProfileSettingsRecord:
    account_id: object
    username: str
    email: str
    display_name: str | None
    phone: str | None
    timezone: str | None
    profile_image_url: str | None
    preferred_language: str | None
    discord_username: str | None
    discord_integration_status: str
    created_at: datetime
    updated_at: datetime


class StubProfileSettingsRepository:
    def __init__(self, record: StubProfileSettingsRecord | None) -> None:
        self._record = record
        self.received_account_ids: list[object] = []
        self.updated_calls: list[dict[str, object]] = []
        self.unit_of_work = StubUnitOfWork()

    def get_profile_settings(self, account_id):  # noqa: ANN001
        self.received_account_ids.append(account_id)
        return self._record

    def update_profile_settings(
        self,
        account_id,  # noqa: ANN001
        *,
        profile_updates: dict[str, object],
        preference_updates: dict[str, object],
    ):
        self.updated_calls.append(
            {
                "account_id": account_id,
                "profile_updates": profile_updates,
                "preference_updates": preference_updates,
            }
        )
        return self._record

    def commit(self) -> None:
        self.unit_of_work.commit()

    def rollback(self) -> None:
        self.unit_of_work.rollback()


class StubUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_profile_settings_service_builds_safe_read_response() -> None:
    account_id = uuid4()
    repository = StubProfileSettingsRepository(
        StubProfileSettingsRecord(
            account_id=account_id,
            username="profile-user",
            email="profile-user@example.com",
            display_name="Profile User",
            phone="+1-312-555-0101",
            timezone="America/Chicago",
            profile_image_url="https://cdn.example.com/profiles/profile-user.png",
            preferred_language="en",
            discord_username="profile-user#1234",
            discord_integration_status="connected",
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )
    service = ProfileSettingsService(repository)

    response = service.get_profile_settings(account_id)

    assert repository.received_account_ids == [account_id]
    assert response.model_dump(mode="json") == {
        "profile": {
            "account_id": str(account_id),
            "username": "profile-user",
            "email": "profile-user@example.com",
            "display_name": "Profile User",
            "phone": "+1-312-555-0101",
            "timezone": "America/Chicago",
            "profile_image_url": "https://cdn.example.com/profiles/profile-user.png",
            "preferred_language": "en",
            "discord": {
                "username": "profile-user#1234",
                "integration_status": "connected",
            },
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T12:30:00Z",
        }
    }


def test_profile_settings_service_raises_not_found_for_missing_record() -> None:
    account_id = uuid4()
    repository = StubProfileSettingsRepository(None)
    service = ProfileSettingsService(repository)

    try:
        service.get_profile_settings(account_id)
    except ProfileSettingsNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing profile settings to raise ProfileSettingsNotFoundError")


def test_profile_settings_service_updates_mutable_fields_only() -> None:
    account_id = uuid4()
    repository = StubProfileSettingsRepository(
        StubProfileSettingsRecord(
            account_id=account_id,
            username="profile-user",
            email="profile-user@example.com",
            display_name="Updated User",
            phone=None,
            timezone="America/New_York",
            profile_image_url=None,
            preferred_language="es",
            discord_username="profile-user#1234",
            discord_integration_status="connected",
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
        )
    )
    service = ProfileSettingsService(repository)

    response = service.update_profile_settings(
        account_id,
        ProfileSettingsUpdateRequest(
            display_name="Updated User",
            timezone="America/New_York",
            preferred_language="es",
        ),
    )

    assert repository.updated_calls == [
        {
            "account_id": account_id,
            "profile_updates": {
                "display_name": "Updated User",
                "timezone": "America/New_York",
            },
            "preference_updates": {"preferred_language": "es"},
        }
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.profile.display_name == "Updated User"
    assert response.profile.preferred_language == "es"


def test_profile_settings_service_rejects_empty_update_payload() -> None:
    repository = StubProfileSettingsRepository(None)
    service = ProfileSettingsService(repository)

    try:
        service.update_profile_settings(uuid4(), ProfileSettingsUpdateRequest())
    except ProfileSettingsUpdateValidationError:
        pass
    else:
        raise AssertionError("Expected empty update payload to raise ProfileSettingsUpdateValidationError")
