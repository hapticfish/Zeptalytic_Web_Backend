from sqlalchemy import MetaData
from alembic.config import Config
from alembic.script import ScriptDirectory

import app.db.models as model_registry
import app.db.bootstrap as bootstrap
from app.db.models.rewards import REWARD_MODEL_MODULES


EXPECTED_REWARD_TABLES = {
    "account_badges",
    "account_objective_progress",
    "badge_definitions",
    "objective_definitions",
    "objective_reward_links",
    "reward_accounts",
    "reward_definitions",
    "reward_events",
    "reward_grants",
    "reward_milestones",
    "reward_notifications",
    "reward_tier_definitions",
}


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
    assert "app.db.models.rewards.account_badges" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.account_objective_progress" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.badge_definitions" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.objective_definitions" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.objective_reward_links" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_accounts" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_definitions" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_events" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_grants" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_milestones" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_notifications" in model_registry.MODEL_MODULES
    assert "app.db.models.rewards.reward_tier_definitions" in model_registry.MODEL_MODULES
    assert "app.db.models.subscription_summaries" in model_registry.MODEL_MODULES


def test_model_registry_uses_rewards_package_registration_source_of_truth() -> None:
    registered_reward_modules = tuple(
        module_name
        for module_name in model_registry.MODEL_MODULES
        if module_name.startswith("app.db.models.rewards.")
    )

    assert registered_reward_modules == REWARD_MODEL_MODULES


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
        "account_badges",
        "account_objective_progress",
        "badge_definitions",
        "objective_definitions",
        "objective_reward_links",
        "reward_accounts",
        "reward_definitions",
        "reward_events",
        "reward_grants",
        "reward_milestones",
        "reward_notifications",
        "reward_tier_definitions",
    }.issubset(set(metadata.tables))


def test_get_target_metadata_registers_exact_rewards_table_surface() -> None:
    metadata = bootstrap.get_target_metadata()
    registered_reward_tables = {
        table_name for table_name in metadata.tables if table_name in EXPECTED_REWARD_TABLES
    }

    assert registered_reward_tables == EXPECTED_REWARD_TABLES


def test_reward_notification_module_and_table_are_registered_for_later_rewards_queue_item() -> None:
    metadata = bootstrap.get_target_metadata()

    assert "app.db.models.rewards.reward_notifications" in model_registry.MODEL_MODULES
    assert "reward_notifications" in metadata.tables


def test_alembic_history_includes_reward_foundation_and_tier_revisions() -> None:
    alembic_config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(alembic_config)
    revision_0245 = script_directory.get_revision("20260416_0245")
    revision_0215 = script_directory.get_revision("20260416_0215")
    revision_0105 = script_directory.get_revision("20260416_0105")
    revision_0010 = script_directory.get_revision("20260416_0010")
    revision_2355 = script_directory.get_revision("20260415_2355")
    revision_2345 = script_directory.get_revision("20260415_2345")
    revision_2315 = script_directory.get_revision("20260415_2315")

    assert revision_0245 is not None
    assert revision_0215 is not None
    assert revision_2315 is not None
    assert revision_2345 is not None
    assert revision_2355 is not None
    assert revision_0010 is not None
    assert revision_0105 is not None
    assert revision_0245.path.endswith("20260416_0245_rdb050_reward_notifications.py")
    assert revision_0215.path.endswith("20260416_0215_rdb040_reward_badge_and_grant_tables.py")
    assert revision_2315.path.endswith("20260415_2315_disc010_profile_discord_fields.py")
    assert revision_2345.path.endswith("20260415_2345_disc020_discord_history_table.py")
    assert revision_2355.path.endswith("20260415_2355_rdb010_reward_foundation_tables.py")
    assert revision_0010.path.endswith("20260416_0010_rdb020_reward_tiers_and_milestones.py")
    assert revision_0105.path.endswith(
        "20260416_0105_rdb030_objective_definition_and_progress_tables.py"
    )
    assert revision_0245.down_revision == "20260416_0215"
    assert revision_0215.down_revision == "20260416_0105"
    assert revision_2345.down_revision == "20260415_2315"
    assert revision_2355.down_revision == "20260415_2345"
    assert revision_0010.down_revision == "20260415_2355"
    assert revision_0105.down_revision == "20260416_0010"
