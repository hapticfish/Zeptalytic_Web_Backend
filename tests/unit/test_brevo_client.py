import httpx
import pytest

from app.core.config import Settings
from app.integrations import (
    BrevoClientConfigurationError,
    BrevoTemplateEmailRequest,
    build_brevo_client,
)


def _build_settings() -> Settings:
    return Settings(
        brevo_api_base_url="https://brevo.test/v3/",
        brevo_api_key="test-brevo-api-key",
        brevo_request_timeout_seconds=15,
    )


def _build_request() -> BrevoTemplateEmailRequest:
    return BrevoTemplateEmailRequest(
        sender_name="Zeptalytic Support",
        sender_email="support@zeptalytic.com",
        reply_to_name="Zeptalytic Support",
        reply_to_email="support@zeptalytic.com",
        to_email="user@example.com",
        to_name="Example User",
        template_id=9,
        params={"verificationUrl": "https://frontend.example.com/verify-email?token=<token>"},
    )


def test_brevo_client_posts_template_email_to_smtp_endpoint() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(201, json={"messageId": "<brevo-message-id@example.test>"})

    client = build_brevo_client(_build_settings(), transport=httpx.MockTransport(handler))

    try:
        result = client.send_template_email(_build_request())
    finally:
        client.close()

    assert result.success is True
    assert result.provider_message_id == "<brevo-message-id@example.test>"
    assert result.failure_code is None
    assert captured_request is not None
    assert str(captured_request.url) == "https://brevo.test/v3/smtp/email"
    assert captured_request.headers["accept"] == "application/json"
    assert captured_request.headers["content-type"] == "application/json"
    assert captured_request.headers["api-key"] == "test-brevo-api-key"
    assert captured_request.read() == (
        b'{"sender":{"name":"Zeptalytic Support","email":"support@zeptalytic.com"},'
        b'"to":[{"email":"user@example.com","name":"Example User"}],'
        b'"replyTo":{"name":"Zeptalytic Support","email":"support@zeptalytic.com"},'
        b'"templateId":9,'
        b'"params":{"verificationUrl":"https://frontend.example.com/verify-email?token=<token>"}}'
    )


def test_build_brevo_client_requires_api_key() -> None:
    with pytest.raises(BrevoClientConfigurationError):
        build_brevo_client(
            Settings(
                brevo_api_base_url="https://brevo.test/v3",
                brevo_api_key=None,
            )
        )


def test_brevo_client_maps_timeout_to_provider_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("brevo timed out", request=request)

    client = build_brevo_client(_build_settings(), transport=httpx.MockTransport(handler))

    try:
        result = client.send_template_email(_build_request())
    finally:
        client.close()

    assert result.success is False
    assert result.failure_code == "provider_timeout"
    assert result.failure_message == "Brevo request timed out."
    assert result.provider_message_id is None


def test_brevo_client_maps_unexpected_status_to_provider_http_error() -> None:
    client = build_brevo_client(
        _build_settings(),
        transport=httpx.MockTransport(lambda request: httpx.Response(400, json={"code": "invalid"})),
    )

    try:
        result = client.send_template_email(_build_request())
    finally:
        client.close()

    assert result.success is False
    assert result.failure_code == "provider_http_error"
    assert result.failure_message == "Brevo returned unexpected status 400."
    assert result.status_code == 400


def test_brevo_client_maps_invalid_json_or_missing_message_id_to_provider_unexpected_response() -> None:
    invalid_json_client = build_brevo_client(
        _build_settings(),
        transport=httpx.MockTransport(lambda request: httpx.Response(201, text="not-json")),
    )

    try:
        invalid_json_result = invalid_json_client.send_template_email(_build_request())
    finally:
        invalid_json_client.close()

    assert invalid_json_result.success is False
    assert invalid_json_result.failure_code == "provider_unexpected_response"
    assert invalid_json_result.failure_message == "Brevo returned invalid JSON."
    assert invalid_json_result.status_code == 201

    missing_message_id_client = build_brevo_client(
        _build_settings(),
        transport=httpx.MockTransport(lambda request: httpx.Response(201, json={"status": "queued"})),
    )

    try:
        missing_message_id_result = missing_message_id_client.send_template_email(_build_request())
    finally:
        missing_message_id_client.close()

    assert missing_message_id_result.success is False
    assert missing_message_id_result.failure_code == "provider_unexpected_response"
    assert missing_message_id_result.failure_message == "Brevo did not return a provider message ID."
    assert missing_message_id_result.status_code == 201
