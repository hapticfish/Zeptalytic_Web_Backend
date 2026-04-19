from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.profile_preferences import ProfilePreference
from app.db.models.profiles import Profile


@dataclass(slots=True)
class ProfileSettingsRecord:
    account_id: UUID
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


class ProfileSettingsRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_profile_settings(self, account_id: UUID) -> ProfileSettingsRecord | None:
        row = self._db.execute(
            select(Account, Profile, ProfilePreference)
            .join(Profile, Profile.account_id == Account.id)
            .join(ProfilePreference, ProfilePreference.account_id == Account.id)
            .where(Account.id == account_id)
        ).one_or_none()
        if row is None:
            return None

        account, profile, preferences = row
        return ProfileSettingsRecord(
            account_id=account.id,
            username=account.username,
            email=account.email,
            display_name=profile.display_name,
            phone=profile.phone,
            timezone=profile.timezone,
            profile_image_url=profile.profile_image_url,
            preferred_language=preferences.preferred_language,
            discord_username=profile.discord_username,
            discord_integration_status=profile.discord_integration_status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
