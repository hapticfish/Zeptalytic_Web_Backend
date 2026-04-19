from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Zeptalytic Web Backend"
    api_v1_prefix: str = "/api/v1"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
