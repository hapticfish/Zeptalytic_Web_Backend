from sqlalchemy import MetaData

import app.db.models as model_registry
import app.db.bootstrap as bootstrap


def test_get_target_metadata_imports_models(monkeypatch) -> None:
    called = False

    def fake_import_models() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(bootstrap, "import_models", fake_import_models)

    metadata = bootstrap.get_target_metadata()

    assert called is True
    assert isinstance(metadata, MetaData)
    assert metadata is bootstrap.Base.metadata


def test_model_registry_imports_split_modules_directly() -> None:
    assert "app.db.models.auth" not in model_registry.MODEL_MODULES
    assert "app.db.models.entitlement_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.payment_method_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.payment_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.product_access_states" in model_registry.MODEL_MODULES
    assert "app.db.models.subscription_summaries" in model_registry.MODEL_MODULES


def test_get_target_metadata_registers_split_model_tables() -> None:
    metadata = bootstrap.get_target_metadata()

    assert {
        "accounts",
        "auth_sessions",
        "email_verification_tokens",
        "password_reset_tokens",
        "account_security_settings",
        "mfa_recovery_codes",
        "auth_events",
        "profiles",
        "profile_preferences",
        "communication_preferences",
        "oauth_connections",
        "addresses",
        "support_tickets",
        "support_ticket_messages",
        "support_ticket_attachments",
        "announcements",
        "service_statuses",
        "subscription_summaries",
        "entitlement_summaries",
        "product_access_states",
        "payment_summaries",
        "payment_method_summaries",
    }.issubset(set(metadata.tables))
