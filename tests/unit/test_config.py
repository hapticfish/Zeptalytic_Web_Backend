from app.core.config import Settings


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        app_env="test",
        app_name="Container Smoke",
        database_url="postgresql+psycopg://postgres:postgres@db:5432/test_db",
        pay_service_base_url="http://pay:8080",
        pay_service_internal_token="test-token",
    )

    assert settings.app_env == "test"
    assert settings.app_name == "Container Smoke"
    assert settings.database_url == "postgresql+psycopg://postgres:postgres@db:5432/test_db"
