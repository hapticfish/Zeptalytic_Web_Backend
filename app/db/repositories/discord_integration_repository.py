from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.discord_connection_history import DiscordConnectionHistory
from app.db.models.profiles import Profile


@dataclass(slots=True)
class DiscordIntegrationRecord:
    account_id: UUID
    discord_user_id: str | None
    discord_username: str | None
    integration_status: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class DiscordConnectionHistoryCreateInput:
    account_id: UUID
    discord_user_id: str
    discord_username: str | None
    status: str


class DiscordIntegrationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def get_integration(self, account_id: UUID) -> DiscordIntegrationRecord | None:
        profile = self._db.get(Profile, account_id)
        if profile is None:
            return None
        return self._to_record(profile)

    def set_current_connection(
        self,
        account_id: UUID,
        *,
        discord_user_id: str,
        discord_username: str | None,
        integration_status: str,
    ) -> DiscordIntegrationRecord | None:
        profile = self._db.get(Profile, account_id)
        if profile is None:
            return None

        profile.discord_user_id = discord_user_id
        profile.discord_username = discord_username
        profile.discord_integration_status = integration_status
        self._db.flush()
        return self._to_record(profile)

    def clear_current_connection(
        self,
        account_id: UUID,
        *,
        integration_status: str,
    ) -> DiscordIntegrationRecord | None:
        profile = self._db.get(Profile, account_id)
        if profile is None:
            return None

        profile.discord_user_id = None
        profile.discord_username = None
        profile.discord_integration_status = integration_status
        self._db.flush()
        return self._to_record(profile)

    def append_history(
        self,
        entry: DiscordConnectionHistoryCreateInput,
    ) -> None:
        self._db.add(
            DiscordConnectionHistory(
                account_id=entry.account_id,
                discord_user_id=entry.discord_user_id,
                discord_username=entry.discord_username,
                status=entry.status,
            )
        )
        self._db.flush()

    @staticmethod
    def _to_record(profile: Profile) -> DiscordIntegrationRecord:
        return DiscordIntegrationRecord(
            account_id=profile.account_id,
            discord_user_id=profile.discord_user_id,
            discord_username=profile.discord_username,
            integration_status=profile.discord_integration_status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
