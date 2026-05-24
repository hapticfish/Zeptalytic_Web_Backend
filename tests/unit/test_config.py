from pathlib import Path

from app.core.config import Settings


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        app_env="test",
        app_name="Container Smoke",
        cors_allowed_origins=("http://localhost:5173", "http://127.0.0.1:5173"),
        cors_allow_credentials=True,
        auth_session_cookie_name="test_session",
        auth_session_ttl_hours=12,
        auth_email_verification_ttl_hours=48,
        auth_password_reset_ttl_hours=4,
        auth_totp_issuer="Test Issuer",
        auth_totp_secret_key="test-secret",
        auth_session_cookie_path="/auth",
        auth_session_cookie_samesite="strict",
        auth_session_cookie_secure=True,
        database_url="postgresql+psycopg://postgres:postgres@db:5432/test_db",
        email_provider="brevo",
        brevo_api_base_url="https://brevo.test/v3",
        brevo_api_key="test-brevo-key",
        brevo_webhook_secret="test-webhook-secret",
        brevo_request_timeout_seconds=15,
        frontend_base_url="https://frontend.example.com",
        email_from_address="hello@example.com",
        email_from_name="Example",
        email_reply_to_address="support@example.com",
        email_support_from_address="support@example.com",
        email_billing_from_address="billing@example.com",
        email_alerts_from_address="alerts@example.com",
        email_updates_from_address="updates@example.com",
        brevo_template_welcome_id=101,
        brevo_template_support_response_id=102,
        brevo_template_order_confirmation_id=103,
        brevo_template_news_updates_id=104,
        brevo_template_failed_signup_id=105,
        brevo_template_email_changed_id=106,
        brevo_template_password_reset_id=107,
        brevo_template_account_details_changed_id=108,
        brevo_template_email_verification_id=109,
        brevo_template_payment_failed_id=110,
        brevo_template_subscription_expiring_id=111,
        pay_service_base_url="http://pay:8080",
        pay_service_internal_token="test-token",
        discord_oauth_base_url="https://discord.com",
        discord_oauth_client_id="discord-client-id",
        discord_oauth_client_secret="discord-client-secret",
        discord_oauth_redirect_uri="https://parent.example.com/api/v1/integrations/discord/callback",
        discord_oauth_state_secret="discord-state-secret",
        discord_oauth_state_ttl_seconds=900,
        security_rate_limit_auth_window_seconds=120,
        security_rate_limit_auth_max_attempts=4,
        security_rate_limit_discord_callback_window_seconds=180,
        security_rate_limit_discord_callback_max_attempts=7,
        security_rate_limit_billing_action_window_seconds=240,
        security_rate_limit_billing_action_max_attempts=8,
        security_rate_limit_support_ticket_window_seconds=3600,
        security_rate_limit_support_ticket_max_attempts=3,
    )

    assert settings.app_env == "test"
    assert settings.app_name == "Container Smoke"
    assert settings.cors_allowed_origins == (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    assert settings.cors_allow_credentials is True
    assert settings.auth_session_cookie_name == "test_session"
    assert settings.auth_session_ttl_hours == 12
    assert settings.auth_email_verification_ttl_hours == 48
    assert settings.auth_password_reset_ttl_hours == 4
    assert settings.auth_totp_issuer == "Test Issuer"
    assert settings.auth_totp_secret_key == "test-secret"
    assert settings.auth_session_cookie_path == "/auth"
    assert settings.auth_session_cookie_samesite == "strict"
    assert settings.auth_session_cookie_secure is True
    assert settings.database_url == "postgresql+psycopg://postgres:postgres@db:5432/test_db"
    assert settings.email_provider == "brevo"
    assert settings.brevo_api_base_url == "https://brevo.test/v3"
    assert settings.brevo_api_key == "test-brevo-key"
    assert settings.brevo_webhook_secret == "test-webhook-secret"
    assert settings.brevo_request_timeout_seconds == 15
    assert settings.frontend_base_url == "https://frontend.example.com"
    assert settings.email_from_address == "hello@example.com"
    assert settings.email_from_name == "Example"
    assert settings.email_reply_to_address == "support@example.com"
    assert settings.email_support_from_address == "support@example.com"
    assert settings.email_billing_from_address == "billing@example.com"
    assert settings.email_alerts_from_address == "alerts@example.com"
    assert settings.email_updates_from_address == "updates@example.com"
    assert settings.brevo_template_welcome_id == 101
    assert settings.brevo_template_support_response_id == 102
    assert settings.brevo_template_order_confirmation_id == 103
    assert settings.brevo_template_news_updates_id == 104
    assert settings.brevo_template_failed_signup_id == 105
    assert settings.brevo_template_email_changed_id == 106
    assert settings.brevo_template_password_reset_id == 107
    assert settings.brevo_template_account_details_changed_id == 108
    assert settings.brevo_template_email_verification_id == 109
    assert settings.brevo_template_payment_failed_id == 110
    assert settings.brevo_template_subscription_expiring_id == 111
    assert settings.pay_service_base_url == "http://pay:8080"
    assert settings.pay_service_internal_token == "test-token"
    assert settings.discord_oauth_base_url == "https://discord.com"
    assert settings.discord_oauth_client_id == "discord-client-id"
    assert settings.discord_oauth_client_secret == "discord-client-secret"
    assert (
        settings.discord_oauth_redirect_uri
        == "https://parent.example.com/api/v1/integrations/discord/callback"
    )
    assert settings.discord_oauth_state_secret == "discord-state-secret"
    assert settings.discord_oauth_state_ttl_seconds == 900
    assert settings.security_rate_limit_auth_window_seconds == 120
    assert settings.security_rate_limit_auth_max_attempts == 4
    assert settings.security_rate_limit_discord_callback_window_seconds == 180
    assert settings.security_rate_limit_discord_callback_max_attempts == 7
    assert settings.security_rate_limit_billing_action_window_seconds == 240
    assert settings.security_rate_limit_billing_action_max_attempts == 8
    assert settings.security_rate_limit_support_ticket_window_seconds == 3600
    assert settings.security_rate_limit_support_ticket_max_attempts == 3


def test_settings_default_frontend_runtime_cors_contract() -> None:
    settings = Settings()

    assert settings.cors_allowed_origins == (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    assert settings.cors_allow_credentials is True


def test_settings_default_email_brevo_contract() -> None:
    settings = Settings()

    assert settings.email_provider == "brevo"
    assert settings.brevo_api_base_url == "https://api.brevo.com/v3"
    assert settings.brevo_api_key is None
    assert settings.brevo_webhook_secret is None
    assert settings.brevo_request_timeout_seconds == 10
    assert settings.frontend_base_url == "http://localhost:5173"
    assert settings.email_from_address == "hello@zeptalytic.com"
    assert settings.email_from_name == "Zeptalytic"
    assert settings.email_reply_to_address == "support@zeptalytic.com"
    assert settings.email_support_from_address == "support@zeptalytic.com"
    assert settings.email_billing_from_address == "billing@zeptalytic.com"
    assert settings.email_alerts_from_address == "alerts@zeptalytic.com"
    assert settings.email_updates_from_address == "updates@zeptalytic.com"
    assert settings.brevo_template_welcome_id == 1
    assert settings.brevo_template_support_response_id == 2
    assert settings.brevo_template_order_confirmation_id == 3
    assert settings.brevo_template_news_updates_id == 4
    assert settings.brevo_template_failed_signup_id == 5
    assert settings.brevo_template_email_changed_id == 6
    assert settings.brevo_template_password_reset_id == 7
    assert settings.brevo_template_account_details_changed_id == 8
    assert settings.brevo_template_email_verification_id == 9
    assert settings.brevo_template_payment_failed_id == 10
    assert settings.brevo_template_subscription_expiring_id == 11


def test_env_example_contains_email_brevo_placeholders_only() -> None:
    env_example = (
        Path(__file__).resolve().parents[2] / ".env.example"
    ).read_text(encoding="utf-8")

    assert "EMAIL_PROVIDER=brevo" in env_example
    assert "BREVO_API_BASE_URL=https://api.brevo.com/v3" in env_example
    assert "BREVO_API_KEY=" in env_example
    assert "BREVO_WEBHOOK_SECRET=" in env_example
    assert "BREVO_REQUEST_TIMEOUT_SECONDS=10" in env_example
    assert "FRONTEND_BASE_URL=http://localhost:5173" in env_example
    assert "EMAIL_FROM_ADDRESS=hello@zeptalytic.com" in env_example
    assert "EMAIL_FROM_NAME=Zeptalytic" in env_example
    assert "EMAIL_REPLY_TO_ADDRESS=support@zeptalytic.com" in env_example
    assert "EMAIL_SUPPORT_FROM_ADDRESS=support@zeptalytic.com" in env_example
    assert "EMAIL_BILLING_FROM_ADDRESS=billing@zeptalytic.com" in env_example
    assert "EMAIL_ALERTS_FROM_ADDRESS=alerts@zeptalytic.com" in env_example
    assert "EMAIL_UPDATES_FROM_ADDRESS=updates@zeptalytic.com" in env_example
    assert "BREVO_TEMPLATE_WELCOME_ID=1" in env_example
    assert "BREVO_TEMPLATE_SUPPORT_RESPONSE_ID=2" in env_example
    assert "BREVO_TEMPLATE_ORDER_CONFIRMATION_ID=3" in env_example
    assert "BREVO_TEMPLATE_NEWS_UPDATES_ID=4" in env_example
    assert "BREVO_TEMPLATE_FAILED_SIGNUP_ID=5" in env_example
    assert "BREVO_TEMPLATE_EMAIL_CHANGED_ID=6" in env_example
    assert "BREVO_TEMPLATE_PASSWORD_RESET_ID=7" in env_example
    assert "BREVO_TEMPLATE_ACCOUNT_DETAILS_CHANGED_ID=8" in env_example
    assert "BREVO_TEMPLATE_EMAIL_VERIFICATION_ID=9" in env_example
    assert "BREVO_TEMPLATE_PAYMENT_FAILED_ID=10" in env_example
    assert "BREVO_TEMPLATE_SUBSCRIPTION_EXPIRING_ID=11" in env_example
    assert "xkeysib-" not in env_example
