import httpx
import pytest

from app.core.config import Settings
from app.integrations import (
    PayClientConfigurationError,
    PayClientInvalidResponseError,
    PayClientUnavailableError,
    build_pay_client,
)


def test_build_pay_client_uses_settings_base_url_and_internal_auth_header() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"ok": True})

    client = build_pay_client(
        Settings(
            pay_service_base_url="http://pay.internal:8080/",
            pay_service_internal_token="internal-token",
        ),
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


def test_build_pay_client_requires_internal_token() -> None:
    with pytest.raises(PayClientConfigurationError):
        build_pay_client(
            Settings(
                pay_service_base_url="http://pay.internal:8080",
                pay_service_internal_token=None,
            )
        )


def test_pay_client_raises_unavailable_error_for_transport_failures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("pay unavailable", request=request)

    client = build_pay_client(
        Settings(
            pay_service_base_url="http://pay.internal:8080",
            pay_service_internal_token="internal-token",
        ),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientUnavailableError):
            client.request_json("GET", "/internal/payment-methods")
    finally:
        client.close()


def test_pay_client_raises_invalid_response_error_for_non_json_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = build_pay_client(
        Settings(
            pay_service_base_url="http://pay.internal:8080",
            pay_service_internal_token="internal-token",
        ),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(PayClientInvalidResponseError):
            client.request_json("GET", "/internal/entitlements")
    finally:
        client.close()
