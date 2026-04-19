from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.profile_settings_repository import ProfileSettingsRepository
from app.schemas.profiles import (
    DiscordProfileDisplaySummary,
    ProfileRouteContractResponse,
    ProfileSettingsReadResponse,
    ProfileSettingsSummary,
    ProfileSettingsUpdateRequest,
)


class ProfileSettingsNotFoundError(Exception):
    """Raised when a profile/settings record does not exist for the requested account."""


class ProfileSettingsUpdateValidationError(Exception):
    """Raised when a profile/settings update request is invalid."""


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

        return self._build_read_response(record)

    def update_profile_settings(
        self,
        account_id,
        payload: ProfileSettingsUpdateRequest,  # noqa: ANN001
    ) -> ProfileSettingsReadResponse:
        raw_updates = payload.model_dump(exclude_unset=True)
        if not raw_updates:
            raise ProfileSettingsUpdateValidationError(
                "At least one mutable profile field must be provided."
            )

        profile_fields = {"display_name", "phone", "timezone", "profile_image_url"}
        profile_updates = {
            field_name: value
            for field_name, value in raw_updates.items()
            if field_name in profile_fields
        }
        preference_updates = {
            field_name: value
            for field_name, value in raw_updates.items()
            if field_name == "preferred_language"
        }

        record = self._repository.update_profile_settings(
            account_id,
            profile_updates=profile_updates,
            preference_updates=preference_updates,
        )
        if record is None:
            self._repository.rollback()
            raise ProfileSettingsNotFoundError(
                f"No profile settings exist for account {account_id}"
            )

        self._repository.commit()
        return self._build_read_response(record)

    @staticmethod
    def _build_read_response(record) -> ProfileSettingsReadResponse:  # noqa: ANN001
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
