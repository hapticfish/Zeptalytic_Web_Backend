from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil
from threading import Lock
from time import monotonic
from uuid import UUID

from fastapi import Request

from app.core.config import Settings


@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    max_attempts: int
    window_seconds: int


class RateLimitExceededError(Exception):
    def __init__(self, *, action: str, retry_after_seconds: int) -> None:
        super().__init__(f"Rate limit exceeded for {action}. Retry after {retry_after_seconds}s.")
        self.action = action
        self.retry_after_seconds = retry_after_seconds


class InMemoryRateLimiter:
    """Process-local phase-1 limiter. Counts reset on process restart and are not shared across nodes."""

    def __init__(self, *, time_provider=monotonic) -> None:
        self._time_provider = time_provider
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, *, action: str, key: str, policy: RateLimitPolicy) -> None:
        now = self._time_provider()
        bucket_key = f"{action}:{key}"
        cutoff = now - policy.window_seconds

        with self._lock:
            hits = self._hits.setdefault(bucket_key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= policy.max_attempts:
                retry_after_seconds = max(1, ceil((hits[0] + policy.window_seconds) - now))
                raise RateLimitExceededError(
                    action=action,
                    retry_after_seconds=retry_after_seconds,
                )

            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def build_request_rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client is not None else "unknown"
    return client_host


def build_authenticated_rate_limit_key(
    request: Request,
    *,
    account_id: UUID | str | None,
) -> str:
    client_host = request.client.host if request.client is not None else "unknown"
    principal = "anonymous" if account_id is None else str(account_id)
    return f"{principal}:{client_host}"


def build_auth_rate_limit_policy(settings: Settings) -> RateLimitPolicy:
    return RateLimitPolicy(
        name="auth_sensitive_flow",
        max_attempts=settings.security_rate_limit_auth_max_attempts,
        window_seconds=settings.security_rate_limit_auth_window_seconds,
    )


def build_discord_callback_rate_limit_policy(settings: Settings) -> RateLimitPolicy:
    return RateLimitPolicy(
        name="discord_callback",
        max_attempts=settings.security_rate_limit_discord_callback_max_attempts,
        window_seconds=settings.security_rate_limit_discord_callback_window_seconds,
    )


def build_billing_action_rate_limit_policy(settings: Settings) -> RateLimitPolicy:
    return RateLimitPolicy(
        name="billing_action",
        max_attempts=settings.security_rate_limit_billing_action_max_attempts,
        window_seconds=settings.security_rate_limit_billing_action_window_seconds,
    )


def build_support_ticket_rate_limit_policy(settings: Settings) -> RateLimitPolicy:
    return RateLimitPolicy(
        name="support_ticket",
        max_attempts=settings.security_rate_limit_support_ticket_max_attempts,
        window_seconds=settings.security_rate_limit_support_ticket_window_seconds,
    )
