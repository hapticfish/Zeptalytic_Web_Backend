import app.db.models as model_registry
import app.db.bootstrap as bootstrap
from app.db.models.rewards import REWARD_MODEL_MODULES


EXPECTED_TABLES = {
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
}


def test_bootstrap_metadata_contains_expected_split_tables() -> None:
    metadata = bootstrap.get_target_metadata()

    assert EXPECTED_TABLES.issubset(set(metadata.tables))


def test_bootstrap_metadata_only_registers_expected_parent_tables() -> None:
    metadata = bootstrap.get_target_metadata()

    assert set(metadata.tables) == EXPECTED_TABLES


def test_rewards_metadata_registration_stays_one_module_per_table() -> None:
    metadata = bootstrap.get_target_metadata()
    registered_reward_modules = tuple(
        module_name
        for module_name in model_registry.MODEL_MODULES
        if module_name.startswith("app.db.models.rewards.")
    )
    reward_tables = {
        table_name for table_name in metadata.tables if table_name in EXPECTED_TABLES and table_name.startswith(
            ("account_badges", "account_objective_progress", "badge_definitions", "objective_definitions", "objective_reward_links", "reward_")
        )
    }

    assert registered_reward_modules == REWARD_MODEL_MODULES
    assert "app.db.models.rewards" not in registered_reward_modules
    assert len(registered_reward_modules) == len(reward_tables)
