"""External integration clients and adapters."""

from app.integrations.discord_oauth_client import (
    DiscordOAuthClient,
    DiscordOAuthConfigurationError,
    DiscordOAuthIdentity,
    DiscordOAuthInvalidResponseError,
    DiscordOAuthStateValidationError,
    DiscordOAuthUnavailableError,
    build_discord_oauth_client,
)
from app.integrations.pay_client import (
    PayClient,
    PayClientConfigurationError,
    PayClientInvalidResponseError,
    PayClientUnavailableError,
    build_pay_client,
)

__all__ = [
    "DiscordOAuthClient",
    "DiscordOAuthConfigurationError",
    "DiscordOAuthIdentity",
    "DiscordOAuthInvalidResponseError",
    "DiscordOAuthStateValidationError",
    "DiscordOAuthUnavailableError",
    "build_discord_oauth_client",
    "PayClient",
    "PayClientConfigurationError",
    "PayClientInvalidResponseError",
    "PayClientUnavailableError",
    "build_pay_client",
]
