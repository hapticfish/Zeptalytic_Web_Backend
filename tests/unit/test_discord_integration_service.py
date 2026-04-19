from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.discord_integration_repository import (
    DiscordConnectionHistoryCreateInput,
)
from app.integrations import DiscordOAuthIdentity, DiscordOAuthStateValidationError
from app.services.discord_integration_service import (
    DiscordIntegrationLinkNotFoundError,
    DiscordIntegrationNotFoundError,
    DiscordIntegrationService,
)


@dataclass
class StubDiscordIntegrationRecord:
    account_id: object
    discord_user_id: str | None
    discord_username: str | None
    integration_status: str
    created_at: datetime
    updated_at: datetime


class StubDiscordIntegrationRepository:
    def __init__(self, record: StubDiscordIntegrationRecord | None) -> None:
        self.record = record
        self.history_entries: list[DiscordConnectionHistoryCreateInput] = []
        self.set_calls: list[dict[str, object]] = []
        self.clear_calls: list[dict[str, object]] = []
        self.received_account_ids: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def get_integration(self, account_id):  # noqa: ANN001
        self.received_account_ids.append(account_id)
        return self.record

    def append_history(self, entry: DiscordConnectionHistoryCreateInput) -> None:
        self.history_entries.append(entry)

    def set_current_connection(
        self,
        account_id,  # noqa: ANN001
        *,
        discord_user_id: str,
        discord_username: str | None,
        integration_status: str,
    ):
        self.set_calls.append(
            {
                "account_id": account_id,
                "discord_user_id": discord_user_id,
                "discord_username": discord_username,
                "integration_status": integration_status,
            }
        )
        if self.record is None:
            return None

        self.record.discord_user_id = discord_user_id
        self.record.discord_username = discord_username
        self.record.integration_status = integration_status
        self.record.updated_at = datetime(2026, 4, 19, 16, 30, tzinfo=timezone.utc)
        return self.record

    def clear_current_connection(
        self,
        account_id,  # noqa: ANN001
        *,
        integration_status: str,
    ):
        self.clear_calls.append(
            {
                "account_id": account_id,
                "integration_status": integration_status,
            }
        )
        if self.record is None:
            return None

        self.record.discord_user_id = None
        self.record.discord_username = None
        self.record.integration_status = integration_status
        self.record.updated_at = datetime(2026, 4, 19, 17, 0, tzinfo=timezone.utc)
        return self.record

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class StubDiscordOAuthClient:
    def __init__(
        self,
        *,
        authorization_url: str = "https://discord.com/oauth2/authorize?state=test",
        identity: DiscordOAuthIdentity | None = None,
        state_error: DiscordOAuthStateValidationError | None = None,
    ) -> None:
        self.authorization_url = authorization_url
        self.identity = identity or DiscordOAuthIdentity(
            discord_user_id="discord-oauth-user",
            discord_username="oauth-user#1234",
        )
        self.state_error = state_error
        self.authorization_account_ids: list[object] = []
        self.validated_states: list[tuple[object, str | None]] = []
        self.codes: list[str] = []

    def build_authorization_url(self, account_id) -> str:  # noqa: ANN001
        self.authorization_account_ids.append(account_id)
        return self.authorization_url

    def validate_state(self, account_id, state: str | None) -> None:  # noqa: ANN001
        self.validated_states.append((account_id, state))
        if self.state_error is not None:
            raise self.state_error

    def exchange_code_for_identity(self, code: str) -> DiscordOAuthIdentity:
        self.codes.append(code)
        return self.identity


def _build_record(
    *,
    discord_user_id: str | None = None,
    discord_username: str | None = None,
    integration_status: str = "pending",
) -> StubDiscordIntegrationRecord:
    return StubDiscordIntegrationRecord(
        account_id=uuid4(),
        discord_user_id=discord_user_id,
        discord_username=discord_username,
        integration_status=integration_status,
        created_at=datetime(2026, 4, 19, 15, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 19, 15, 5, tzinfo=timezone.utc),
    )


def test_discord_integration_service_builds_safe_read_response() -> None:
    repository = StubDiscordIntegrationRepository(
        _build_record(
            discord_user_id="discord-internal-123",
            discord_username="profile-user#1234",
            integration_status="connected",
        )
    )
    service = DiscordIntegrationService(repository)

    response = service.get_integration(repository.record.account_id)

    assert repository.received_account_ids == [repository.record.account_id]
    assert response.model_dump(mode="json") == {
        "discord": {
            "account_id": str(repository.record.account_id),
            "username": "profile-user#1234",
            "integration_status": "connected",
            "created_at": "2026-04-19T15:00:00Z",
            "updated_at": "2026-04-19T15:05:00Z",
        }
    }
    assert "discord_user_id" not in response.model_dump()


def test_discord_integration_service_connects_initial_account_and_records_history() -> None:
    record = _build_record()
    repository = StubDiscordIntegrationRepository(record)
    service = DiscordIntegrationService(repository)

    response = service.connect_discord_account(
        record.account_id,
        discord_user_id="discord-123",
        discord_username="linked-user#9999",
    )

    assert repository.set_calls == [
        {
            "account_id": record.account_id,
            "discord_user_id": "discord-123",
            "discord_username": "linked-user#9999",
            "integration_status": "connected",
        }
    ]
    assert repository.history_entries == [
        DiscordConnectionHistoryCreateInput(
            account_id=record.account_id,
            discord_user_id="discord-123",
            discord_username="linked-user#9999",
            status="connected",
        )
    ]
    assert repository.commits == 1
    assert repository.rollbacks == 0
    assert response.discord.username == "linked-user#9999"
    assert response.discord.integration_status == "connected"


def test_discord_integration_service_builds_connect_url_from_oauth_client() -> None:
    record = _build_record()
    oauth_client = StubDiscordOAuthClient()
    service = DiscordIntegrationService(
        StubDiscordIntegrationRepository(record),
        oauth_client=oauth_client,
    )

    authorization_url = service.build_connect_url(record.account_id)

    assert authorization_url == "https://discord.com/oauth2/authorize?state=test"
    assert oauth_client.authorization_account_ids == [record.account_id]


def test_discord_integration_service_completes_oauth_callback_after_state_validation() -> None:
    record = _build_record()
    repository = StubDiscordIntegrationRepository(record)
    oauth_client = StubDiscordOAuthClient(
        identity=DiscordOAuthIdentity(
            discord_user_id="discord-oauth-123",
            discord_username="oauth-user#5678",
        )
    )
    service = DiscordIntegrationService(repository, oauth_client=oauth_client)

    response = service.complete_oauth_callback(
        record.account_id,
        code="oauth-code-123",
        state="signed-state",
    )

    assert oauth_client.validated_states == [(record.account_id, "signed-state")]
    assert oauth_client.codes == ["oauth-code-123"]
    assert repository.set_calls == [
        {
            "account_id": record.account_id,
            "discord_user_id": "discord-oauth-123",
            "discord_username": "oauth-user#5678",
            "integration_status": "connected",
        }
    ]
    assert response.discord.username == "oauth-user#5678"


def test_discord_integration_service_stops_on_invalid_oauth_state() -> None:
    record = _build_record()
    repository = StubDiscordIntegrationRepository(record)
    oauth_client = StubDiscordOAuthClient(
        state_error=DiscordOAuthStateValidationError("invalid_state_signature")
    )
    service = DiscordIntegrationService(repository, oauth_client=oauth_client)

    try:
        service.complete_oauth_callback(
            record.account_id,
            code="oauth-code-123",
            state="bad-state",
        )
    except DiscordOAuthStateValidationError as exc:
        assert exc.reason == "invalid_state_signature"
    else:
        raise AssertionError("Expected invalid OAuth state to raise DiscordOAuthStateValidationError")

    assert oauth_client.codes == []
    assert repository.set_calls == []
    assert repository.history_entries == []
    assert repository.commits == 0
    assert repository.rollbacks == 0


def test_discord_integration_service_reconnects_different_account_and_preserves_prior_history() -> None:
    record = _build_record(
        discord_user_id="discord-old",
        discord_username="old-user#1111",
        integration_status="connected",
    )
    repository = StubDiscordIntegrationRepository(record)
    service = DiscordIntegrationService(repository)

    response = service.connect_discord_account(
        record.account_id,
        discord_user_id="discord-new",
        discord_username="new-user#2222",
    )

    assert repository.history_entries == [
        DiscordConnectionHistoryCreateInput(
            account_id=record.account_id,
            discord_user_id="discord-old",
            discord_username="old-user#1111",
            status="disconnected",
        ),
        DiscordConnectionHistoryCreateInput(
            account_id=record.account_id,
            discord_user_id="discord-new",
            discord_username="new-user#2222",
            status="connected",
        ),
    ]
    assert repository.commits == 1
    assert repository.rollbacks == 0
    assert response.discord.username == "new-user#2222"
    assert response.discord.integration_status == "connected"


def test_discord_integration_service_disconnects_active_link_and_preserves_history() -> None:
    record = _build_record(
        discord_user_id="discord-123",
        discord_username="linked-user#9999",
        integration_status="connected",
    )
    repository = StubDiscordIntegrationRepository(record)
    service = DiscordIntegrationService(repository)

    response = service.disconnect_discord_account(record.account_id)

    assert repository.history_entries == [
        DiscordConnectionHistoryCreateInput(
            account_id=record.account_id,
            discord_user_id="discord-123",
            discord_username="linked-user#9999",
            status="disconnected",
        )
    ]
    assert repository.clear_calls == [
        {
            "account_id": record.account_id,
            "integration_status": "disconnected",
        }
    ]
    assert repository.commits == 1
    assert repository.rollbacks == 0
    assert response.discord.username is None
    assert response.discord.integration_status == "disconnected"


def test_discord_integration_service_raises_for_missing_profile_row() -> None:
    repository = StubDiscordIntegrationRepository(None)
    service = DiscordIntegrationService(repository)

    try:
        service.get_integration(uuid4())
    except DiscordIntegrationNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing integration state to raise DiscordIntegrationNotFoundError")


def test_discord_integration_service_raises_for_disconnect_without_active_link() -> None:
    record = _build_record(integration_status="disconnected")
    repository = StubDiscordIntegrationRepository(record)
    service = DiscordIntegrationService(repository)

    try:
        service.disconnect_discord_account(record.account_id)
    except DiscordIntegrationLinkNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing active Discord link to raise DiscordIntegrationLinkNotFoundError")
