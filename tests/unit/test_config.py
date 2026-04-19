from app.core.config import Settings


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        app_env="test",
        app_name="Container Smoke",
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
        pay_service_base_url="http://pay:8080",
        pay_service_internal_token="test-token",
    )

    assert settings.app_env == "test"
    assert settings.app_name == "Container Smoke"
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
