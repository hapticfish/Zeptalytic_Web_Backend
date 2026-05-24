from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Zeptalytic Web Backend"
    api_v1_prefix: str = "/api/v1"

    # Browser/runtime integration contract for local React/Vite frontend.
    # Keep these explicit. Do not use wildcard origins with credentialed CORS.
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: tuple[str, ...] = (
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    )
    cors_allow_headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    )

    auth_session_cookie_name: str = "zeptalytic_session"
    auth_session_ttl_hours: int = 24 * 30
    auth_email_verification_ttl_hours: int = 24
    auth_password_reset_ttl_hours: int = 2
    auth_totp_issuer: str = "Zeptalytic"
    auth_totp_secret_key: str = "dev-insecure-change-me"
    auth_session_cookie_path: str = "/"
    auth_session_cookie_samesite: str = "lax"
    auth_session_cookie_secure: bool = False

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/zeptalytic_web_backend"

    email_provider: str = "brevo"
    brevo_api_base_url: str = "https://api.brevo.com/v3"
    brevo_api_key: str | None = None
    brevo_webhook_secret: str | None = None
    brevo_request_timeout_seconds: int = 10

    frontend_base_url: str = "http://localhost:5173"

    email_from_address: str = "hello@zeptalytic.com"
    email_from_name: str = "Zeptalytic"
    email_reply_to_address: str = "support@zeptalytic.com"

    email_support_from_address: str = "support@zeptalytic.com"
    email_billing_from_address: str = "billing@zeptalytic.com"
    email_alerts_from_address: str = "alerts@zeptalytic.com"
    email_updates_from_address: str = "updates@zeptalytic.com"

    brevo_template_welcome_id: int = 1
    brevo_template_support_response_id: int = 2
    brevo_template_order_confirmation_id: int = 3
    brevo_template_news_updates_id: int = 4
    brevo_template_failed_signup_id: int = 5
    brevo_template_email_changed_id: int = 6
    brevo_template_password_reset_id: int = 7
    brevo_template_account_details_changed_id: int = 8
    brevo_template_email_verification_id: int = 9
    brevo_template_payment_failed_id: int = 10
    brevo_template_subscription_expiring_id: int = 11

    pay_service_base_url: str = "http://localhost:8080"
    pay_service_internal_token: str | None = None

    discord_oauth_base_url: str = "https://discord.com"
    discord_oauth_client_id: str | None = None
    discord_oauth_client_secret: str | None = None
    discord_oauth_redirect_uri: str | None = None
    discord_oauth_state_secret: str = "dev-discord-oauth-state-secret"
    discord_oauth_state_ttl_seconds: int = 600

    security_rate_limit_auth_window_seconds: int = 300
    security_rate_limit_auth_max_attempts: int = 5
    security_rate_limit_discord_callback_window_seconds: int = 300
    security_rate_limit_discord_callback_max_attempts: int = 10
    security_rate_limit_billing_action_window_seconds: int = 300
    security_rate_limit_billing_action_max_attempts: int = 10
    security_rate_limit_support_ticket_window_seconds: int = 3600
    security_rate_limit_support_ticket_max_attempts: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
