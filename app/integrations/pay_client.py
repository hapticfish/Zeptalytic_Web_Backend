from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import jwt

from app.core.config import Settings, settings


class PayClientConfigurationError(Exception):
    """Raised when the Pay client cannot be constructed from app settings."""


class PayClientUnavailableError(Exception):
    """Raised when the Pay service cannot be reached."""


class PayClientInvalidResponseError(Exception):
    """Raised when the Pay service returns an unexpected or invalid response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PayInternalJwtConfig:
    issuer: str
    audience: str
    caller: str
    algorithm: str
    private_key: str
    ttl_seconds: int


@dataclass(frozen=True, slots=True)
class PayAuthContext:
    account_id: UUID
    scope: str


_INTERNAL_ACCOUNT_ROUTE_RE = re.compile(
    r"^/internal/accounts/(?P<account_id>[0-9a-fA-F-]{36})/(?P<resource>[^/?#]+)"
)


class PayClient:
    def __init__(
        self,
        *,
        base_url: str,
        internal_token: str | None = None,
        internal_jwt: PayInternalJwtConfig | None = None,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url:
            raise PayClientConfigurationError("Pay service base URL must be configured.")

        if internal_jwt is None and not internal_token:
            raise PayClientConfigurationError(
                "Pay service internal JWT settings or legacy internal token must be configured."
            )

        self._internal_token = internal_token
        self._internal_jwt = internal_jwt
        self._client = httpx.Client(
            base_url=normalized_base_url,
            headers={"Accept": "application/json"},
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
        account_id: UUID | str | None = None,
        scope: str | None = None,
    ) -> Any:
        expected_codes = expected_status_codes or {200}
        auth_context = self._resolve_auth_context(
            method=method,
            path=path,
            account_id=account_id,
            scope=scope,
        )

        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json_body,
                headers=self._build_auth_headers(auth_context),
            )
        except httpx.HTTPError as exc:
            raise PayClientUnavailableError("Pay service is unavailable.") from exc

        if response.status_code not in expected_codes:
            raise PayClientInvalidResponseError(
                f"Pay service returned unexpected status {response.status_code}.",
                status_code=response.status_code,
                response_body=self._safe_response_body(response),
            )

        try:
            return response.json()
        except ValueError as exc:
            raise PayClientInvalidResponseError(
                "Pay service returned invalid JSON.",
                status_code=response.status_code,
                response_body=response.text,
            ) from exc

    def close(self) -> None:
        self._client.close()

    def _resolve_auth_context(
        self,
        *,
        method: str,
        path: str,
        account_id: UUID | str | None,
        scope: str | None,
    ) -> PayAuthContext | None:
        if account_id is not None and scope is not None:
            return PayAuthContext(account_id=self._coerce_account_id(account_id), scope=scope)

        inferred_context = self._infer_account_scoped_auth_context(method=method, path=path)
        if inferred_context is not None:
            return inferred_context

        if account_id is not None or scope is not None:
            raise PayClientConfigurationError(
                "Both account_id and scope are required for explicit Pay JWT auth context."
            )

        return None

    def _build_auth_headers(self, auth_context: PayAuthContext | None) -> dict[str, str]:
        if auth_context is not None and self._internal_jwt is not None:
            return {"Authorization": f"Bearer {self._mint_internal_jwt(auth_context)}"}

        if self._internal_token:
            return {"Authorization": f"Bearer {self._internal_token}"}

        raise PayClientConfigurationError(
            "Pay service internal JWT settings are required for account-scoped Pay routes."
        )

    def _mint_internal_jwt(self, auth_context: PayAuthContext) -> str:
        assert self._internal_jwt is not None

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=self._internal_jwt.ttl_seconds)
        payload = {
            "sub": self._internal_jwt.caller,
            "service": self._internal_jwt.caller,
            "iss": self._internal_jwt.issuer,
            "aud": self._internal_jwt.audience,
            "iat": now,
            "exp": expires_at,
            "account_id": str(auth_context.account_id),
            "scope": auth_context.scope,
            "scp": [auth_context.scope],
        }
        return jwt.encode(
            payload,
            self._internal_jwt.private_key,
            algorithm=self._internal_jwt.algorithm,
        )

    @staticmethod
    def _infer_account_scoped_auth_context(*, method: str, path: str) -> PayAuthContext | None:
        normalized_path = path if path.startswith("/") else f"/{path}"
        match = _INTERNAL_ACCOUNT_ROUTE_RE.match(normalized_path)
        if match is None:
            return None

        account_id = PayClient._coerce_account_id(match.group("account_id"))
        resource = match.group("resource")
        normalized_method = method.upper()

        if normalized_method == "GET" and resource == "projection-summary":
            return PayAuthContext(account_id=account_id, scope="pay:projection")

        if normalized_method == "POST" and resource == "billing":
            return PayAuthContext(account_id=account_id, scope="pay:billing")

        return None

    @staticmethod
    def _coerce_account_id(value: UUID | str) -> UUID:
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except ValueError as exc:
            raise PayClientConfigurationError("Pay auth account_id must be a valid UUID.") from exc

    @staticmethod
    def _safe_response_body(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text


def _build_internal_jwt_config(active_settings: Settings) -> PayInternalJwtConfig | None:
    private_key = active_settings.normalized_pay_service_internal_jwt_private_key
    if private_key is None:
        return None

    if active_settings.pay_service_internal_jwt_ttl_seconds <= 0:
        raise PayClientConfigurationError("Pay service internal JWT TTL must be greater than zero.")

    return PayInternalJwtConfig(
        issuer=active_settings.pay_service_internal_jwt_issuer,
        audience=active_settings.pay_service_internal_jwt_audience,
        caller=active_settings.pay_service_internal_jwt_caller,
        algorithm=active_settings.pay_service_internal_jwt_algorithm,
        private_key=private_key,
        ttl_seconds=active_settings.pay_service_internal_jwt_ttl_seconds,
    )


def build_pay_client(
    app_settings: Settings | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> PayClient:
    active_settings = app_settings or settings
    return PayClient(
        base_url=active_settings.pay_service_base_url,
        internal_token=active_settings.pay_service_internal_token,
        internal_jwt=_build_internal_jwt_config(active_settings),
        transport=transport,
    )