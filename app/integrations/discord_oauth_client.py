from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx

from app.core.config import Settings, settings


class DiscordOAuthConfigurationError(Exception):
    """Raised when Discord OAuth settings are incomplete."""


class DiscordOAuthUnavailableError(Exception):
    """Raised when Discord OAuth cannot be reached."""


class DiscordOAuthInvalidResponseError(Exception):
    """Raised when Discord OAuth returns an unexpected payload."""


class DiscordOAuthStateValidationError(Exception):
    """Raised when the Discord OAuth state is missing, invalid, or expired."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class DiscordOAuthIdentity:
    discord_user_id: str
    discord_username: str | None


class DiscordOAuthClient:
    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        state_secret: str,
        state_ttl_seconds: int = 600,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url:
            raise DiscordOAuthConfigurationError("Discord OAuth base URL must be configured.")
        if not client_id:
            raise DiscordOAuthConfigurationError("Discord OAuth client ID must be configured.")
        if not client_secret:
            raise DiscordOAuthConfigurationError("Discord OAuth client secret must be configured.")
        if not redirect_uri:
            raise DiscordOAuthConfigurationError("Discord OAuth redirect URI must be configured.")
        if not state_secret:
            raise DiscordOAuthConfigurationError("Discord OAuth state secret must be configured.")
        if state_ttl_seconds <= 0:
            raise DiscordOAuthConfigurationError("Discord OAuth state TTL must be positive.")

        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._state_secret = state_secret.encode("utf-8")
        self._state_ttl = timedelta(seconds=state_ttl_seconds)
        self._base_url = normalized_base_url
        self._client = httpx.Client(
            base_url=normalized_base_url,
            headers={"Accept": "application/json"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def build_authorization_url(self, account_id: UUID) -> str:
        state = self.generate_state(account_id)
        query = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_uri": self._redirect_uri,
                "scope": "identify",
                "state": state,
                "prompt": "consent",
            }
        )
        return f"{self._base_url}/oauth2/authorize?{query}"

    def generate_state(
        self,
        account_id: UUID,
        *,
        issued_at: datetime | None = None,
    ) -> str:
        timestamp = int((issued_at or datetime.now(timezone.utc)).timestamp())
        payload = json.dumps(
            {"account_id": str(account_id), "issued_at": timestamp},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        signature = hmac.new(self._state_secret, payload, hashlib.sha256).digest()
        return (
            f"{self._urlsafe_b64encode(payload)}."
            f"{self._urlsafe_b64encode(signature)}"
        )

    def validate_state(
        self,
        account_id: UUID,
        state: str | None,
        *,
        now: datetime | None = None,
    ) -> None:
        if not state:
            raise DiscordOAuthStateValidationError("missing_state")

        try:
            encoded_payload, encoded_signature = state.split(".", maxsplit=1)
        except ValueError as exc:
            raise DiscordOAuthStateValidationError("malformed_state") from exc

        payload = self._urlsafe_b64decode(encoded_payload, reason="malformed_state")
        provided_signature = self._urlsafe_b64decode(
            encoded_signature,
            reason="malformed_state",
        )
        expected_signature = hmac.new(self._state_secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise DiscordOAuthStateValidationError("invalid_state_signature")

        try:
            decoded_payload = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DiscordOAuthStateValidationError("malformed_state") from exc

        if decoded_payload.get("account_id") != str(account_id):
            raise DiscordOAuthStateValidationError("account_mismatch")

        issued_at_raw = decoded_payload.get("issued_at")
        if not isinstance(issued_at_raw, int):
            raise DiscordOAuthStateValidationError("malformed_state")

        issued_at = datetime.fromtimestamp(issued_at_raw, tz=timezone.utc)
        active_now = now or datetime.now(timezone.utc)
        if active_now - issued_at > self._state_ttl:
            raise DiscordOAuthStateValidationError("expired_state")

    def exchange_code_for_identity(self, code: str) -> DiscordOAuthIdentity:
        normalized_code = code.strip()
        if not normalized_code:
            raise DiscordOAuthInvalidResponseError("Discord OAuth code is required.")

        token_payload = self._request_json(
            "POST",
            "/api/oauth2/token",
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "authorization_code",
                "code": normalized_code,
                "redirect_uri": self._redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise DiscordOAuthInvalidResponseError(
                "Discord OAuth token exchange did not return an access token."
            )

        identity_payload = self._request_json(
            "GET",
            "/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        discord_user_id = identity_payload.get("id")
        if not isinstance(discord_user_id, str) or not discord_user_id:
            raise DiscordOAuthInvalidResponseError(
                "Discord OAuth user lookup did not return a valid Discord user ID."
            )

        username = identity_payload.get("username")
        discriminator = identity_payload.get("discriminator")
        return DiscordOAuthIdentity(
            discord_user_id=discord_user_id,
            discord_username=self._format_username(username, discriminator),
        )

    def close(self) -> None:
        self._client.close()

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.request(method=method, url=path, data=data, headers=headers)
        except httpx.HTTPError as exc:
            raise DiscordOAuthUnavailableError("Discord OAuth is unavailable.") from exc

        if response.status_code != 200:
            raise DiscordOAuthInvalidResponseError(
                f"Discord OAuth returned unexpected status {response.status_code}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise DiscordOAuthInvalidResponseError(
                "Discord OAuth returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise DiscordOAuthInvalidResponseError(
                "Discord OAuth returned an unexpected response payload."
            )
        return payload

    @staticmethod
    def _format_username(username: Any, discriminator: Any) -> str | None:
        if not isinstance(username, str) or not username.strip():
            return None
        normalized_username = username.strip()
        if isinstance(discriminator, str) and discriminator and discriminator != "0":
            return f"{normalized_username}#{discriminator}"
        return normalized_username

    @staticmethod
    def _urlsafe_b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _urlsafe_b64decode(value: str, *, reason: str) -> bytes:
        try:
            padding = "=" * (-len(value) % 4)
            return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise DiscordOAuthStateValidationError(reason) from exc


def build_discord_oauth_client(
    app_settings: Settings | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> DiscordOAuthClient:
    active_settings = app_settings or settings
    return DiscordOAuthClient(
        base_url=active_settings.discord_oauth_base_url,
        client_id=active_settings.discord_oauth_client_id or "",
        client_secret=active_settings.discord_oauth_client_secret or "",
        redirect_uri=active_settings.discord_oauth_redirect_uri or "",
        state_secret=active_settings.discord_oauth_state_secret,
        state_ttl_seconds=active_settings.discord_oauth_state_ttl_seconds,
        transport=transport,
    )
