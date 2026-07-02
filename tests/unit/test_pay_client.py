from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import jwt
import pytest

from app.core.config import Settings
from app.integrations import (
    PayClientConfigurationError,
    PayClientInvalidResponseError,
    PayClientUnavailableError,
    build_pay_client,
)


JWT_SECRET = "test-pay-internal-jwt-secret"
JWT_ISSUER = "https://auth.example.test/"
JWT_AUDIENCE = "zeptalytic-pay-service"
JWT_CALLER = "zeptalytic_web"


def _build_legacy_token_settings() -> Settings:
    return Settings(
        pay_service_base_url="http://pay.internal:8080/",
        pay_service_internal_token="internal-token",
        pay_service_internal_jwt_private_key=None,
    )


def _build_internal_jwt_settings(
    *,
    include_legacy_token: bool = True,
    ttl_seconds: int = 300,
) -> Settings:
    return Settings(
        pay_service_base_url="http://pay.internal:8080/",
        pay_service_internal_token="legacy-token" if include_legacy_token else None,
        pay_service_internal_jwt_issuer=JWT_ISSUER,
        pay_service_internal_jwt_audience=JWT_AUDIENCE,
        pay_service_internal_jwt_caller=JWT_CALLER,
        pay_service_internal_jwt_algorithm="HS256",
        pay_service_internal_jwt_private_key=JWT_SECRET,
        pay_service_internal_jwt_ttl_seconds=ttl_seconds,
    )


def _authorization_token(request: httpx.Request) -> str:
    authorization = request.headers["authorization"]
    assert authorization.startswith("Bearer ")
    return authorization.removeprefix("Bearer ")


def _decode_internal_jwt(token: str) -> dict[str, object]:
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )


def test_build_pay_client_uses_settings_base_url_and_legacy_internal_auth_header() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_legacy_token_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        payload = client.request_json("GET", "/internal/subscription-summary")
    finally:
        client.close()

    assert payload == {"ok": True}
    assert captured_request is not None
    assert str(captured_request.url) == "http://pay.internal:8080/internal/subscription-summary"
    assert captured_request.headers["authorization"] == "Bearer internal-token"
    assert captured_request.headers["accept"] == "application/json"


def test_build_pay_client_requires_internal_token_or_internal_jwt() -> None:
    with pytest.raises(PayClientConfigurationError):
        build_pay_client(
            Settings(
                pay_service_base_url="http://pay.internal:8080",
                pay_service_internal_token=None,
                pay_service_internal_jwt_private_key=None,
            )
        )


def test_build_pay_client_requires_positive_internal_jwt_ttl() -> None:
    with pytest.raises(PayClientConfigurationError):
        build_pay_client(
            _build_internal_jwt_settings(
                include_legacy_token=False,
                ttl_seconds=0,
            )
        )


def test_pay_client_mints_projection_scope_jwt_for_account_projection_route() -> None:
    account_id = uuid4()
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=True),
        transport=httpx.MockTransport(handler),
    )

    try:
        payload = client.request_json(
            "GET",
            f"/internal/accounts/{account_id}/projection-summary",
        )
    finally:
        client.close()

    assert payload == {"ok": True}
    assert captured_request is not None

    token = _authorization_token(captured_request)
    assert token != "legacy-token"

    claims = _decode_internal_jwt(token)
    assert claims["sub"] == JWT_CALLER
    assert claims["service"] == JWT_CALLER
    assert claims["iss"] == JWT_ISSUER
    assert claims["aud"] == JWT_AUDIENCE
    assert claims["account_id"] == str(account_id)
    assert claims["scope"] == "pay:projection"
    assert claims["scp"] == ["pay:projection"]


@pytest.mark.parametrize(
    "path_suffix",
    [
        "/billing/checkout",
        "/billing/subscription-change",
        "/billing/subscription-cancel",
        "/billing/subscription-restart",
        "/billing/promo-code/validate",
        "/billing/promo-code/apply",
        "/billing/discount-offer/claim",
    ],
)
def test_pay_client_mints_billing_scope_jwt_for_account_billing_routes(
    path_suffix: str,
) -> None:
    account_id = uuid4()
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=True),
        transport=httpx.MockTransport(handler),
    )

    try:
        payload = client.request_json(
            "POST",
            f"/internal/accounts/{account_id}{path_suffix}",
            json_body={"idempotency_key": "test-key"},
        )
    finally:
        client.close()

    assert payload == {"ok": True}
    assert captured_request is not None
    assert captured_request.method == "POST"

    token = _authorization_token(captured_request)
    assert token != "legacy-token"

    claims = _decode_internal_jwt(token)
    assert claims["account_id"] == str(account_id)
    assert claims["scope"] == "pay:billing"
    assert claims["scp"] == ["pay:billing"]


def test_pay_client_can_use_explicit_account_scoped_jwt_context() -> None:
    account_id = uuid4()
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=False),
        transport=httpx.MockTransport(handler),
    )

    try:
        payload = client.request_json(
            "POST",
            "/internal/custom-account-action",
            json_body={"ok": True},
            account_id=account_id,
            scope="pay:billing",
        )
    finally:
        client.close()

    assert payload == {"ok": True}
    assert captured_request is not None

    claims = _decode_internal_jwt(_authorization_token(captured_request))
    assert claims["account_id"] == str(account_id)
    assert claims["scope"] == "pay:billing"
    assert claims["scp"] == ["pay:billing"]


@pytest.mark.parametrize(
    "account_id, scope",
    [
        (uuid4(), None),
        (None, "pay:billing"),
    ],
)
def test_pay_client_requires_complete_explicit_account_scoped_auth_context(
    account_id: UUID | None,
    scope: str | None,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=False),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientConfigurationError):
            client.request_json(
                "POST",
                "/internal/custom-account-action",
                json_body={"ok": True},
                account_id=account_id,
                scope=scope,
            )
    finally:
        client.close()


def test_pay_client_rejects_invalid_explicit_account_id_for_jwt_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=False),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientConfigurationError):
            client.request_json(
                "POST",
                "/internal/custom-account-action",
                json_body={"ok": True},
                account_id="not-a-uuid",
                scope="pay:billing",
            )
    finally:
        client.close()


def test_pay_client_requires_legacy_token_for_non_account_routes_when_only_jwt_is_configured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        _build_internal_jwt_settings(include_legacy_token=False),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientConfigurationError):
            client.request_json("GET", "/internal/subscription-summary")
    finally:
        client.close()


def test_pay_client_raises_unavailable_error_for_transport_failures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("pay unavailable", request=request)

    client = build_pay_client(
        _build_legacy_token_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientUnavailableError):
            client.request_json("GET", "/internal/payment-methods")
    finally:
        client.close()


def test_pay_client_raises_invalid_response_error_for_unexpected_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "error": {
                    "code": "conflict",
                    "message": "Conflict.",
                }
            },
        )

    client = build_pay_client(
        _build_legacy_token_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientInvalidResponseError) as exc_info:
            client.request_json("GET", "/internal/entitlements")
    finally:
        client.close()

    assert exc_info.value.status_code == 409
    assert exc_info.value.response_body == {
        "error": {
            "code": "conflict",
            "message": "Conflict.",
        }
    }


def test_pay_client_raises_invalid_response_error_for_non_json_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = build_pay_client(
        _build_legacy_token_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientInvalidResponseError):
            client.request_json("GET", "/internal/entitlements")
    finally:
        client.close()