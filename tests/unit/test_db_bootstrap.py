from sqlalchemy import MetaData
from alembic.config import Config
from alembic.script import ScriptDirectory

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
    assert "app.db.models.discord_connection_history" in model_registry.MODEL_MODULES
    assert "app.db.models.entitlement_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.payment_method_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.payment_summaries" in model_registry.MODEL_MODULES
    assert "app.db.models.product_access_states" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_accounts" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_events" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_milestones" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_tier_definitions" in model_registry.MODEL_MODULES
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
        "discord_connection_history",
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
        "reward_accounts",
        "reward_events",
        "reward_milestones",
        "reward_tier_definitions",
    }.issubset(set(metadata.tables))


def test_later_rewards_modules_and_tables_are_not_registered_before_later_rewards_items() -> None:
    metadata = bootstrap.get_target_metadata()
    reward_tables = {
        "reward_definitions",
        "reward_grants",
        "objective_definitions",
        "objective_reward_links",
        "account_objective_progress",
        "badge_definitions",
        "account_badges",
        "reward_notifications",
    }

    assert "app.db.models.rewards.reward_accounts" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_events" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_milestones" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_tier_definitions" in model_registry.MODEL_MODULES
    assert reward_tables.isdisjoint(set(metadata.tables))


def test_alembic_history_includes_reward_foundation_and_tier_revisions() -> None:
    alembic_config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(alembic_config)
    revision_0010 = script_directory.get_revision("20260416_0010")
    revision_2355 = script_directory.get_revision("20260415_2355")
    revision_2345 = script_directory.get_revision("20260415_2345")
    revision_2315 = script_directory.get_revision("20260415_2315")

    assert revision_2315 is not None
    assert revision_2345 is not None
    assert revision_2355 is not None
    assert revision_0010 is not None
    assert revision_2315.path.endswith("20260415_2315_disc010_profile_discord_fields.py")
    assert revision_2345.path.endswith("20260415_2345_disc020_discord_history_table.py")
    assert revision_2355.path.endswith("20260415_2355_rdb010_reward_foundation_tables.py")
    assert revision_0010.path.endswith("20260416_0010_rdb020_reward_tiers_and_milestones.py")
    assert revision_2345.down_revision == "20260415_2315"
    assert revision_2355.down_revision == "20260415_2345"
    assert revision_0010.down_revision == "20260415_2355"
