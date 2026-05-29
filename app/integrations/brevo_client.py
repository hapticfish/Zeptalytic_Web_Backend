from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings, settings


class BrevoClientConfigurationError(Exception):
    """Raised when the Brevo client cannot be constructed from app settings."""


@dataclass(frozen=True, slots=True)
class BrevoTemplateEmailRequest:
    sender_name: str
    sender_email: str
    reply_to_name: str
    reply_to_email: str
    to_email: str
    to_name: str | None
    template_id: int
    params: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BrevoSendEmailResult:
    provider_message_id: str | None
    failure_code: str | None = None
    failure_message: str | None = None
    status_code: int | None = None

    @property
    def success(self) -> bool:
        return self.failure_code is None


class BrevoClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url:
            raise BrevoClientConfigurationError("Brevo API base URL must be configured.")
        if not api_key:
            raise BrevoClientConfigurationError("Brevo API key must be configured.")
        if timeout_seconds <= 0:
            raise BrevoClientConfigurationError("Brevo request timeout must be positive.")

        self._client = httpx.Client(
            base_url=normalized_base_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "api-key": api_key,
            },
            timeout=timeout_seconds,
            transport=transport,
        )

    def send_template_email(
        self,
        request: BrevoTemplateEmailRequest,
    ) -> BrevoSendEmailResult:
        payload: dict[str, Any] = {
            "sender": {
                "name": request.sender_name,
                "email": request.sender_email,
            },
            "to": [
                {
                    "email": request.to_email,
                }
            ],
            "replyTo": {
                "name": request.reply_to_name,
                "email": request.reply_to_email,
            },
            "templateId": request.template_id,
        }
        if request.to_name:
            payload["to"][0]["name"] = request.to_name
        if request.params:
            payload["params"] = dict(request.params)

        try:
            response = self._client.post("/smtp/email", json=payload)
        except httpx.TimeoutException:
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_timeout",
                failure_message="Brevo request timed out.",
            )
        except httpx.HTTPError:
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_http_error",
                failure_message="Brevo request failed.",
            )

        if response.status_code != 201:
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_http_error",
                failure_message=f"Brevo returned unexpected status {response.status_code}.",
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError:
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_unexpected_response",
                failure_message="Brevo returned invalid JSON.",
                status_code=response.status_code,
            )

        if not isinstance(payload, dict):
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_unexpected_response",
                failure_message="Brevo returned an unexpected response payload.",
                status_code=response.status_code,
            )

        message_id = payload.get("messageId")
        if not isinstance(message_id, str) or not message_id:
            return BrevoSendEmailResult(
                provider_message_id=None,
                failure_code="provider_unexpected_response",
                failure_message="Brevo did not return a provider message ID.",
                status_code=response.status_code,
            )

        return BrevoSendEmailResult(
            provider_message_id=message_id,
            status_code=response.status_code,
        )

    def close(self) -> None:
        self._client.close()


def build_brevo_client(
    app_settings: Settings | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> BrevoClient:
    active_settings = app_settings or settings
    return BrevoClient(
        base_url=active_settings.brevo_api_base_url,
        api_key=active_settings.active_brevo_api_key or "",
        timeout_seconds=active_settings.brevo_request_timeout_seconds,
        transport=transport,
    )
