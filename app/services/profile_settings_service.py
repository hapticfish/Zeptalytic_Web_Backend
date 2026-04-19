from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.profile_settings_repository import ProfileSettingsRepository
from app.schemas.profiles import (
    DiscordProfileDisplaySummary,
    ProfileRouteContractResponse,
    ProfileSettingsReadResponse,
    ProfileSettingsSummary,
)


class ProfileSettingsNotFoundError(Exception):
    """Raised when a profile/settings record does not exist for the requested account."""


class ProfileSettingsService:
    def __init__(self, repository: ProfileSettingsRepository) -> None:
        self._repository = repository

    def describe_contract(self) -> ProfileRouteContractResponse:
        return ProfileRouteContractResponse()

    def get_profile_settings(self, account_id) -> ProfileSettingsReadResponse:  # noqa: ANN001
        record = self._repository.get_profile_settings(account_id)
        if record is None:
            raise ProfileSettingsNotFoundError(
                f"No profile settings exist for account {account_id}"
            )

        return ProfileSettingsReadResponse(
            profile=ProfileSettingsSummary(
                account_id=record.account_id,
                username=record.username,
                email=record.email,
                display_name=record.display_name,
                phone=record.phone,
                timezone=record.timezone,
                profile_image_url=record.profile_image_url,
                preferred_language=record.preferred_language,
                discord=DiscordProfileDisplaySummary(
                    username=record.discord_username,
                    integration_status=record.discord_integration_status,
                ),
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
        )


def build_profile_settings_service(db: Session) -> ProfileSettingsService:
    return ProfileSettingsService(ProfileSettingsRepository(db))
