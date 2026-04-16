import app.db.bootstrap as bootstrap


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
    "reward_accounts",
    "reward_events",
}


def test_bootstrap_metadata_contains_expected_split_tables() -> None:
    metadata = bootstrap.get_target_metadata()

    assert EXPECTED_TABLES.issubset(set(metadata.tables))


def test_bootstrap_metadata_only_registers_expected_parent_tables() -> None:
    metadata = bootstrap.get_target_metadata()

    assert set(metadata.tables) == EXPECTED_TABLES
