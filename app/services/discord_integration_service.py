from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.discord_integration_repository import (
    DiscordConnectionHistoryCreateInput,
    DiscordIntegrationRecord,
    DiscordIntegrationRepository,
)
from app.integrations import DiscordOAuthClient
from app.schemas.integrations import DiscordIntegrationReadResponse, DiscordIntegrationSummary


class DiscordIntegrationNotFoundError(Exception):
    """Raised when an account does not have a Discord integration profile row."""


class DiscordIntegrationLinkNotFoundError(Exception):
    """Raised when a disconnect is requested without an active Discord linkage."""


class DiscordIntegrationService:
    def __init__(
        self,
        repository: DiscordIntegrationRepository,
        oauth_client: DiscordOAuthClient | None = None,
    ) -> None:
        self._repository = repository
        self._oauth_client = oauth_client

    def get_integration(self, account_id) -> DiscordIntegrationReadResponse:  # noqa: ANN001
        record = self._repository.get_integration(account_id)
        if record is None:
            raise DiscordIntegrationNotFoundError(
                f"No Discord integration state exists for account {account_id}"
            )

        return self._build_read_response(record)

    def build_connect_url(self, account_id) -> str:  # noqa: ANN001
        oauth_client = self._require_oauth_client()
        return oauth_client.build_authorization_url(account_id)

    def complete_oauth_callback(
        self,
        account_id,
        *,
        code: str,
        state: str | None,
    ) -> DiscordIntegrationReadResponse:  # noqa: ANN001
        oauth_client = self._require_oauth_client()
        oauth_client.validate_state(account_id, state)
        identity = oauth_client.exchange_code_for_identity(code)
        return self.connect_discord_account(
            account_id,
            discord_user_id=identity.discord_user_id,
            discord_username=identity.discord_username,
        )

    def connect_discord_account(
        self,
        account_id,
        *,
        discord_user_id: str,
        discord_username: str | None,
    ) -> DiscordIntegrationReadResponse:  # noqa: ANN001
        record = self._repository.get_integration(account_id)
        if record is None:
            raise DiscordIntegrationNotFoundError(
                f"No Discord integration state exists for account {account_id}"
            )

        normalized_user_id = discord_user_id.strip()
        normalized_username = None if discord_username is None else discord_username.strip() or None
        if not normalized_user_id:
            raise ValueError("Discord user ID is required.")

        try:
            if (
                record.discord_user_id is not None
                and record.discord_user_id != normalized_user_id
            ):
                self._repository.append_history(
                    DiscordConnectionHistoryCreateInput(
                        account_id=record.account_id,
                        discord_user_id=record.discord_user_id,
                        discord_username=record.discord_username,
                        status="disconnected",
                    )
                )

            updated = self._repository.set_current_connection(
                account_id,
                discord_user_id=normalized_user_id,
                discord_username=normalized_username,
                integration_status="connected",
            )
            if updated is None:
                raise DiscordIntegrationNotFoundError(
                    f"No Discord integration state exists for account {account_id}"
                )

            self._repository.append_history(
                DiscordConnectionHistoryCreateInput(
                    account_id=updated.account_id,
                    discord_user_id=normalized_user_id,
                    discord_username=normalized_username,
                    status="connected",
                )
            )
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise

        return self._build_read_response(updated)

    def disconnect_discord_account(
        self,
        account_id,
    ) -> DiscordIntegrationReadResponse:  # noqa: ANN001
        record = self._repository.get_integration(account_id)
        if record is None:
            raise DiscordIntegrationNotFoundError(
                f"No Discord integration state exists for account {account_id}"
            )
        if record.discord_user_id is None:
            raise DiscordIntegrationLinkNotFoundError(
                f"No active Discord connection exists for account {account_id}"
            )

        try:
            self._repository.append_history(
                DiscordConnectionHistoryCreateInput(
                    account_id=record.account_id,
                    discord_user_id=record.discord_user_id,
                    discord_username=record.discord_username,
                    status="disconnected",
                )
            )
            updated = self._repository.clear_current_connection(
                account_id,
                integration_status="disconnected",
            )
            if updated is None:
                raise DiscordIntegrationNotFoundError(
                    f"No Discord integration state exists for account {account_id}"
                )
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise

        return self._build_read_response(updated)

    @staticmethod
    def _build_read_response(record: DiscordIntegrationRecord) -> DiscordIntegrationReadResponse:
        return DiscordIntegrationReadResponse(
            discord=DiscordIntegrationSummary(
                account_id=record.account_id,
                username=record.discord_username,
                integration_status=record.integration_status,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
        )

    def _require_oauth_client(self) -> DiscordOAuthClient:
        if self._oauth_client is None:
            raise RuntimeError("Discord OAuth client is not configured for this service instance.")
        return self._oauth_client


def build_discord_integration_service(
    db: Session,
    oauth_client: DiscordOAuthClient | None = None,
) -> DiscordIntegrationService:
    return DiscordIntegrationService(DiscordIntegrationRepository(db), oauth_client=oauth_client)
