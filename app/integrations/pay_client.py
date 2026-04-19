from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from app.core.config import Settings, settings


class PayClientConfigurationError(Exception):
    """Raised when the Pay client cannot be constructed from app settings."""


class PayClientUnavailableError(Exception):
    """Raised when the Pay service cannot be reached."""


class PayClientInvalidResponseError(Exception):
    """Raised when the Pay service returns an unexpected or invalid response."""


class PayClient:
    def __init__(
        self,
        *,
        base_url: str,
        internal_token: str,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url:
            raise PayClientConfigurationError("Pay service base URL must be configured.")
        if not internal_token:
            raise PayClientConfigurationError("Pay service internal token must be configured.")

        self._client = httpx.Client(
            base_url=normalized_base_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {internal_token}",
            },
            timeout=timeout_seconds,
            transport=transport,
        )

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        expected_status_codes: set[int] | None = None,
    ) -> Any:
        expected_codes = expected_status_codes or {200}

        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json_body,
            )
        except httpx.HTTPError as exc:
            raise PayClientUnavailableError("Pay service is unavailable.") from exc

        if response.status_code not in expected_codes:
            raise PayClientInvalidResponseError(
                f"Pay service returned unexpected status {response.status_code}."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise PayClientInvalidResponseError("Pay service returned invalid JSON.") from exc

    def close(self) -> None:
        self._client.close()


def build_pay_client(
    app_settings: Settings | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> PayClient:
    active_settings = app_settings or settings
    return PayClient(
        base_url=active_settings.pay_service_base_url,
        internal_token=active_settings.pay_service_internal_token or "",
        transport=transport,
    )
