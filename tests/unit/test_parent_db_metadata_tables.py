import app.db.bootstrap as bootstrap


IDENTITY_AND_SECURITY_TABLES = {
    "accounts",
    "auth_sessions",
    "email_verification_tokens",
    "password_reset_tokens",
    "account_security_settings",
    "mfa_recovery_codes",
    "auth_events",
}

PROFILE_AND_SETTINGS_TABLES = {
    "profiles",
    "profile_preferences",
    "communication_preferences",
    "oauth_connections",
    "addresses",
}

SUPPORT_AND_CONTENT_TABLES = {
    "support_tickets",
    "support_ticket_messages",
    "support_ticket_attachments",
    "announcements",
    "service_statuses",
}

PAY_DERIVED_PROJECTION_TABLES = {
    "subscription_summaries",
    "entitlement_summaries",
    "product_access_states",
    "payment_summaries",
    "payment_method_summaries",
}

EXPECTED_PARENT_TABLES = (
    IDENTITY_AND_SECURITY_TABLES
    | PROFILE_AND_SETTINGS_TABLES
    | SUPPORT_AND_CONTENT_TABLES
    | PAY_DERIVED_PROJECTION_TABLES
)


def test_parent_db_metadata_registers_identity_and_security_tables() -> None:
    metadata_tables = set(bootstrap.get_target_metadata().tables)

    assert IDENTITY_AND_SECURITY_TABLES.issubset(metadata_tables)


def test_parent_db_metadata_registers_profile_and_settings_tables() -> None:
    metadata_tables = set(bootstrap.get_target_metadata().tables)

    assert PROFILE_AND_SETTINGS_TABLES.issubset(metadata_tables)


def test_parent_db_metadata_registers_support_and_content_tables() -> None:
    metadata_tables = set(bootstrap.get_target_metadata().tables)

    assert SUPPORT_AND_CONTENT_TABLES.issubset(metadata_tables)


def test_parent_db_metadata_registers_pay_projection_tables() -> None:
    metadata_tables = set(bootstrap.get_target_metadata().tables)

    assert PAY_DERIVED_PROJECTION_TABLES.issubset(metadata_tables)


def test_parent_db_metadata_only_contains_expected_parent_tables() -> None:
    metadata_tables = set(bootstrap.get_target_metadata().tables)

    assert metadata_tables == EXPECTED_PARENT_TABLES
