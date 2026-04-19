from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Zeptalytic Web Backend"
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    cors_allow_credentials: bool = True
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
