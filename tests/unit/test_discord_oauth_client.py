from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.integrations import (
    DiscordOAuthConfigurationError,
    DiscordOAuthIdentity,
    DiscordOAuthInvalidResponseError,
    DiscordOAuthStateValidationError,
    DiscordOAuthUnavailableError,
    build_discord_oauth_client,
)


def _build_settings() -> Settings:
    return Settings(
        discord_oauth_base_url="https://discord.com",
        discord_oauth_client_id="discord-client-id",
        discord_oauth_client_secret="discord-client-secret",
        discord_oauth_redirect_uri="https://parent.example.com/api/v1/integrations/discord/callback",
        discord_oauth_state_secret="discord-state-secret",
        discord_oauth_state_ttl_seconds=600,
    )


def test_discord_oauth_client_builds_authorization_url_with_signed_state() -> None:
    account_id = uuid4()
    client = build_discord_oauth_client(_build_settings())

    try:
        authorization_url = client.build_authorization_url(account_id)
        parsed_url = urlparse(authorization_url)
        query = parse_qs(parsed_url.query)
    finally:
        client.close()

    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "discord.com"
    assert parsed_url.path == "/oauth2/authorize"
    assert query["client_id"] == ["discord-client-id"]
    assert query["response_type"] == ["code"]
    assert query["redirect_uri"] == [
        "https://parent.example.com/api/v1/integrations/discord/callback"
    ]
    assert query["scope"] == ["identify"]
    assert query["prompt"] == ["consent"]
    assert len(query["state"][0]) > 20


def test_discord_oauth_client_rejects_missing_or_expired_state() -> None:
    account_id = uuid4()
    client = build_discord_oauth_client(_build_settings())

    try:
        with pytest.raises(DiscordOAuthStateValidationError) as missing_state_exc:
            client.validate_state(account_id, None)

        expired_state = client.generate_state(
            account_id,
            issued_at=datetime.now(timezone.utc) - timedelta(seconds=601),
        )
        with pytest.raises(DiscordOAuthStateValidationError) as expired_state_exc:
            client.validate_state(account_id, expired_state)
    finally:
        client.close()

    assert missing_state_exc.value.reason == "missing_state"
    assert expired_state_exc.value.reason == "expired_state"


def test_discord_oauth_client_rejects_state_for_different_account() -> None:
    source_account_id = uuid4()
    other_account_id = uuid4()
    client = build_discord_oauth_client(_build_settings())

    try:
        state = client.generate_state(source_account_id)
        with pytest.raises(DiscordOAuthStateValidationError) as exc_info:
            client.validate_state(other_account_id, state)
    finally:
        client.close()

    assert exc_info.value.reason == "account_mismatch"


def test_discord_oauth_client_exchanges_code_for_discord_identity() -> None:
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        if request.url.path == "/api/oauth2/token":
            body = request.read().decode("utf-8")
            assert "client_id=discord-client-id" in body
            assert "client_secret=discord-client-secret" in body
            assert "grant_type=authorization_code" in body
            assert "code=discord-auth-code" in body
            return httpx.Response(200, json={"access_token": "discord-access-token"})
        if request.url.path == "/api/users/@me":
            assert request.headers["authorization"] == "Bearer discord-access-token"
            return httpx.Response(
                200,
                json={"id": "discord-user-123", "username": "linked-user", "discriminator": "4242"},
            )
        raise AssertionError(f"Unexpected Discord OAuth request path: {request.url.path}")

    client = build_discord_oauth_client(
        _build_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        identity = client.exchange_code_for_identity("discord-auth-code")
    finally:
        client.close()

    assert identity == DiscordOAuthIdentity(
        discord_user_id="discord-user-123",
        discord_username="linked-user#4242",
    )
    assert [request.url.path for request in captured_requests] == [
        "/api/oauth2/token",
        "/api/users/@me",
    ]


def test_discord_oauth_client_surfaces_transport_and_payload_failures() -> None:
    def unavailable_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("discord unavailable", request=request)

    unavailable_client = build_discord_oauth_client(
        _build_settings(),
        transport=httpx.MockTransport(unavailable_handler),
    )

    try:
        with pytest.raises(DiscordOAuthUnavailableError):
            unavailable_client.exchange_code_for_identity("discord-auth-code")
    finally:
        unavailable_client.close()

    invalid_payload_client = build_discord_oauth_client(
        _build_settings(),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="not-json")),
    )

    try:
        with pytest.raises(DiscordOAuthInvalidResponseError):
            invalid_payload_client.exchange_code_for_identity("discord-auth-code")
    finally:
        invalid_payload_client.close()


def test_discord_oauth_client_requires_complete_configuration() -> None:
    with pytest.raises(DiscordOAuthConfigurationError):
        build_discord_oauth_client(
            Settings(
                discord_oauth_base_url="https://discord.com",
                discord_oauth_client_id=None,
                discord_oauth_client_secret="discord-client-secret",
                discord_oauth_redirect_uri="https://parent.example.com/callback",
                discord_oauth_state_secret="discord-state-secret",
            )
        )
