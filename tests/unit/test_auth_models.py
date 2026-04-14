from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.auth import (
    Account,
    AccountSecuritySettings,
    Announcement,
    Address,
    AuthEvent,
    AuthSession,
    CommunicationPreference,
    EmailVerificationToken,
    MfaRecoveryCode,
    OAuthConnection,
    PasswordResetToken,
    Profile,
    ProfilePreference,
    ServiceStatus,
    SupportTicketAttachment,
    SupportTicket,
    SupportTicketMessage,
)


def _create_in_memory_schema() -> tuple[Session, MetaData]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    metadata = MetaData()

    for table in (
        Account.__table__,
        AuthSession.__table__,
        EmailVerificationToken.__table__,
        PasswordResetToken.__table__,
        AccountSecuritySettings.__table__,
        MfaRecoveryCode.__table__,
        AuthEvent.__table__,
        Profile.__table__,
        ProfilePreference.__table__,
        CommunicationPreference.__table__,
        OAuthConnection.__table__,
        Address.__table__,
        SupportTicket.__table__,
        SupportTicketMessage.__table__,
        SupportTicketAttachment.__table__,
        Announcement.__table__,
        ServiceStatus.__table__,
    ):
        table.to_metadata(metadata)

    metadata.create_all(engine)
    return Session(engine), metadata


def test_auth_tables_are_registered_in_metadata() -> None:
    table_names = set(Account.metadata.tables)

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
    }.issubset(table_names)


def test_accounts_table_has_expected_constraints_and_indexes() -> None:
    accounts_table = Account.__table__
    constraint_columns = {
        tuple(sorted(column.name for column in constraint.columns))
        for constraint in accounts_table.constraints
        if getattr(constraint, "columns", None)
    }
    index_names = {index.name for index in accounts_table.indexes}

    assert ("email",) in constraint_columns
    assert ("username",) in constraint_columns
    assert "ix_accounts_status" in index_names


def test_security_tables_have_expected_defaults_and_indexes() -> None:
    security_table = AccountSecuritySettings.__table__
    communication_table = CommunicationPreference.__table__
    recovery_code_indexes = {index.name for index in MfaRecoveryCode.__table__.indexes}
    auth_event_indexes = {index.name for index in AuthEvent.__table__.indexes}

    assert security_table.c.two_factor_enabled.server_default is not None
    assert security_table.c.recovery_methods_available_count.server_default is not None
    assert communication_table.c.marketing_emails_enabled.server_default is not None
    assert communication_table.c.product_updates_enabled.server_default is not None
    assert communication_table.c.announcement_emails_enabled.server_default is not None
    assert "ix_mfa_recovery_codes_account_id" in recovery_code_indexes
    assert "ix_auth_events_account_id" in auth_event_indexes
    assert "ix_auth_events_event_type" in auth_event_indexes


def test_oauth_connections_have_expected_indexes() -> None:
    oauth_indexes = {index.name for index in OAuthConnection.__table__.indexes}

    assert "ix_oauth_connections_account_id" in oauth_indexes
    assert "uq_oauth_connections_provider_user" in oauth_indexes


def test_addresses_have_expected_defaults_and_indexes() -> None:
    addresses_table = Address.__table__
    address_indexes = {index.name for index in addresses_table.indexes}

    assert addresses_table.c.is_primary.server_default is not None
    assert "ix_addresses_account_id" in address_indexes
    assert "ix_addresses_account_id_address_type" in address_indexes


def test_support_tables_have_expected_defaults_constraints_and_indexes() -> None:
    support_ticket_table = SupportTicket.__table__
    support_message_table = SupportTicketMessage.__table__
    support_attachment_table = SupportTicketAttachment.__table__
    ticket_constraint_columns = {
        tuple(sorted(column.name for column in constraint.columns))
        for constraint in support_ticket_table.constraints
        if getattr(constraint, "columns", None)
    }
    ticket_indexes = {index.name for index in support_ticket_table.indexes}
    message_indexes = {index.name for index in support_message_table.indexes}
    attachment_constraint_columns = {
        tuple(sorted(column.name for column in constraint.columns))
        for constraint in support_attachment_table.constraints
        if getattr(constraint, "columns", None)
    }
    attachment_indexes = {index.name for index in support_attachment_table.indexes}

    assert ("ticket_code",) in ticket_constraint_columns
    assert "ix_support_tickets_account_id" in ticket_indexes
    assert "ix_support_tickets_status" in ticket_indexes
    assert support_message_table.c.is_internal_note.server_default is not None
    assert "ix_support_ticket_messages_ticket_id" in message_indexes
    assert "ix_support_ticket_messages_account_id" in message_indexes
    assert ("storage_key",) in attachment_constraint_columns
    assert "ix_support_ticket_attachments_ticket_id" in attachment_indexes
    assert "ix_support_ticket_attachments_uploaded_by_account_id" in attachment_indexes
    assert "ix_support_ticket_attachments_scan_status" in attachment_indexes


def test_content_status_tables_have_expected_defaults() -> None:
    announcement_table = Announcement.__table__
    service_status_table = ServiceStatus.__table__

    assert announcement_table.c.created_at.server_default is not None
    assert announcement_table.c.updated_at.server_default is not None
    assert service_status_table.c.updated_at.server_default is not None


def test_auth_and_security_persistence_round_trip() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        username="tester",
        email="tester@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.flush()

    auth_session = AuthSession(
        account_id=account.id,
        session_token_hash="session-token-hash",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        ip_address="203.0.113.25",
        user_agent="pytest-agent",
    )
    email_token = EmailVerificationToken(
        account_id=account.id,
        token_hash="verify-token-hash",
        expires_at=datetime.now(UTC) + timedelta(hours=12),
    )
    reset_token = PasswordResetToken(
        account_id=account.id,
        token_hash="reset-token-hash",
        expires_at=datetime.now(UTC) + timedelta(hours=2),
    )
    security_settings = AccountSecuritySettings(account_id=account.id)
    recovery_code = MfaRecoveryCode(
        account_id=account.id,
        code_hash="recovery-code-hash",
    )
    auth_event = AuthEvent(
        account_id=account.id,
        event_type="login_success",
        ip_address="203.0.113.25",
        user_agent="pytest-agent",
        event_metadata={"source": "unit-test"},
    )
    profile = Profile(
        account_id=account.id,
        display_name="Test Runner",
        phone="+1-555-0100",
        timezone="America/Chicago",
        profile_image_url="https://cdn.example.com/avatar.png",
        discord_username="testrunner",
    )
    profile_preferences = ProfilePreference(
        account_id=account.id,
        preferred_language="en-US",
    )
    communication_preferences = CommunicationPreference(account_id=account.id)
    oauth_connection = OAuthConnection(
        account_id=account.id,
        provider="discord",
        provider_user_id="discord-user-123",
        provider_username="testrunner#1234",
        status="connected",
        connection_metadata={"guilds": 2},
    )
    address = Address(
        account_id=account.id,
        address_type="billing",
        label="Primary billing",
        full_name="Test Runner",
        line1="100 Example Street",
        line2="Suite 200",
        city_or_locality="Chicago",
        state_or_region="IL",
        postal_code="60601",
        country_code="US",
        country_name="United States",
        formatted_address="Test Runner, 100 Example Street, Suite 200, Chicago, IL 60601, United States",
        is_primary=True,
    )
    support_ticket = SupportTicket(
        account_id=account.id,
        ticket_code="SUP-1001",
        request_type="billing",
        related_product_code="zardbot",
        priority="normal",
        subject="Need billing help",
        description="I need help updating my billing address.",
        status="open",
        estimated_response_sla_label="Within 24 hours",
    )
    announcement = Announcement(
        scope="global",
        product_code="zardbot",
        title="Planned maintenance",
        body="Short maintenance window tonight.",
        severity="info",
        published_at=datetime.now(UTC),
    )
    service_status = ServiceStatus(
        product_code="zardbot",
        status="operational",
        message="All systems normal.",
    )

    session.add_all(
        [
            auth_session,
            email_token,
            reset_token,
            security_settings,
            recovery_code,
            auth_event,
            profile,
            profile_preferences,
            communication_preferences,
            oauth_connection,
            address,
            support_ticket,
            announcement,
            service_status,
        ]
    )
    session.flush()

    support_message = SupportTicketMessage(
        ticket_id=support_ticket.id,
        account_id=account.id,
        author_type="account",
        message_body="The issue happens when I try to save the billing form.",
    )
    internal_note = SupportTicketMessage(
        ticket_id=support_ticket.id,
        author_type="support_agent",
        message_body="Reproduced locally and escalated.",
        is_internal_note=True,
    )
    attachment = SupportTicketAttachment(
        ticket_id=support_ticket.id,
        uploaded_by_account_id=account.id,
        storage_key="support/SUP-1001/attachment-1",
        original_filename="billing-screenshot.png",
        content_type="image/png",
        file_size_bytes=24576,
        scan_status="pending",
    )
    session.add_all([support_message, internal_note, attachment])
    session.commit()

    persisted_session = session.scalar(select(AuthSession).where(AuthSession.account_id == account.id))
    persisted_verify = session.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.account_id == account.id)
    )
    persisted_reset = session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.account_id == account.id)
    )
    persisted_security_settings = session.scalar(
        select(AccountSecuritySettings).where(AccountSecuritySettings.account_id == account.id)
    )
    persisted_recovery_code = session.scalar(
        select(MfaRecoveryCode).where(MfaRecoveryCode.account_id == account.id)
    )
    persisted_auth_event = session.scalar(select(AuthEvent).where(AuthEvent.account_id == account.id))
    persisted_profile = session.scalar(select(Profile).where(Profile.account_id == account.id))
    persisted_profile_preferences = session.scalar(
        select(ProfilePreference).where(ProfilePreference.account_id == account.id)
    )
    persisted_communication_preferences = session.scalar(
        select(CommunicationPreference).where(CommunicationPreference.account_id == account.id)
    )
    persisted_oauth_connection = session.scalar(
        select(OAuthConnection).where(OAuthConnection.account_id == account.id)
    )
    persisted_address = session.scalar(select(Address).where(Address.account_id == account.id))
    persisted_support_ticket = session.scalar(select(SupportTicket).where(SupportTicket.account_id == account.id))
    persisted_support_messages = session.scalars(
        select(SupportTicketMessage).where(SupportTicketMessage.ticket_id == support_ticket.id)
    ).all()
    persisted_support_attachment = session.scalar(
        select(SupportTicketAttachment).where(SupportTicketAttachment.ticket_id == support_ticket.id)
    )
    persisted_announcement = session.scalar(select(Announcement).where(Announcement.scope == "global"))
    persisted_service_status = session.scalar(
        select(ServiceStatus).where(ServiceStatus.product_code == "zardbot")
    )

    assert persisted_session is not None
    assert persisted_session.session_token_hash == "session-token-hash"
    assert persisted_verify is not None
    assert persisted_verify.token_hash == "verify-token-hash"
    assert persisted_reset is not None
    assert persisted_reset.token_hash == "reset-token-hash"
    assert persisted_security_settings is not None
    assert persisted_security_settings.two_factor_enabled is False
    assert persisted_security_settings.recovery_methods_available_count == 0
    assert persisted_recovery_code is not None
    assert persisted_recovery_code.code_hash == "recovery-code-hash"
    assert persisted_auth_event is not None
    assert persisted_auth_event.event_type == "login_success"
    assert persisted_auth_event.event_metadata == {"source": "unit-test"}
    assert persisted_profile is not None
    assert persisted_profile.display_name == "Test Runner"
    assert persisted_profile.timezone == "America/Chicago"
    assert persisted_profile.account.id == account.id
    assert persisted_profile_preferences is not None
    assert persisted_profile_preferences.preferred_language == "en-US"
    assert persisted_communication_preferences is not None
    assert persisted_communication_preferences.marketing_emails_enabled is False
    assert persisted_communication_preferences.product_updates_enabled is True
    assert persisted_communication_preferences.announcement_emails_enabled is True
    assert persisted_oauth_connection is not None
    assert persisted_oauth_connection.provider == "discord"
    assert persisted_oauth_connection.provider_user_id == "discord-user-123"
    assert persisted_oauth_connection.connection_metadata == {"guilds": 2}
    assert persisted_address is not None
    assert persisted_address.address_type == "billing"
    assert persisted_address.country_code == "US"
    assert persisted_address.is_primary is True
    assert persisted_support_ticket is not None
    assert persisted_support_ticket.ticket_code == "SUP-1001"
    assert persisted_support_ticket.related_product_code == "zardbot"
    assert len(persisted_support_messages) == 2
    assert persisted_support_messages[0].ticket.id == support_ticket.id
    assert persisted_support_messages[0].author_type == "account"
    assert persisted_support_messages[0].author_account is not None
    assert persisted_support_messages[1].is_internal_note is True
    assert persisted_support_messages[1].author_account is None
    assert persisted_support_attachment is not None
    assert persisted_support_attachment.storage_key == "support/SUP-1001/attachment-1"
    assert persisted_support_attachment.original_filename == "billing-screenshot.png"
    assert persisted_support_attachment.uploaded_by_account.id == account.id
    assert persisted_announcement is not None
    assert persisted_announcement.title == "Planned maintenance"
    assert persisted_announcement.severity == "info"
    assert persisted_service_status is not None
    assert persisted_service_status.status == "operational"
    assert persisted_service_status.message == "All systems normal."
    assert account.profile is not None
    assert account.profile.discord_username == "testrunner"
    assert account.profile_preferences is not None
    assert account.profile_preferences.preferred_language == "en-US"
    assert account.communication_preferences is not None
    assert account.communication_preferences.product_updates_enabled is True
    assert len(account.oauth_connections) == 1
    assert account.oauth_connections[0].provider_username == "testrunner#1234"
    assert len(account.addresses) == 1
    assert account.addresses[0].city_or_locality == "Chicago"
    assert len(account.support_tickets) == 1
    assert account.support_tickets[0].subject == "Need billing help"
    assert len(account.support_tickets[0].messages) == 2
    assert len(account.support_tickets[0].attachments) == 1
    assert account.support_tickets[0].attachments[0].scan_status == "pending"
    assert len(account.uploaded_support_ticket_attachments) == 1


def test_accounts_reject_duplicate_email() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        Account(
            username="tester-1",
            email="duplicate@example.com",
            password_hash="hash-1",
            status="active",
            role="member",
        )
    )
    session.commit()

    session.add(
        Account(
            username="tester-2",
            email="duplicate@example.com",
            password_hash="hash-2",
            status="active",
            role="member",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_auth_sessions_require_token_hash() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        AuthSession(
            account_id=account.id,
            session_token_hash=None,  # type: ignore[arg-type]
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_account_security_settings_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(AccountSecuritySettings(account_id=uuid4()))

    with pytest.raises(IntegrityError):
        session.commit()


def test_auth_events_require_event_type() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        AuthEvent(
            account_id=account.id,
            event_type=None,  # type: ignore[arg-type]
            event_metadata={},
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_profiles_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(Profile(account_id=uuid4(), display_name="Orphan"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_profiles_enforce_one_to_one_account_mapping() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="profile-owner",
        email="profile-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(Profile(account_id=account.id, display_name="First Profile"))
    session.commit()

    session.add(Profile(account_id=account.id, display_name="Duplicate Profile"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_profile_preferences_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(ProfilePreference(account_id=uuid4(), preferred_language="en-US"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_communication_preferences_enforce_one_to_one_account_mapping() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="prefs-owner",
        email="prefs-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(CommunicationPreference(account_id=account.id))
    session.commit()

    session.add(CommunicationPreference(account_id=account.id))

    with pytest.raises(IntegrityError):
        session.commit()


def test_oauth_connections_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        OAuthConnection(
            account_id=uuid4(),
            provider="discord",
            provider_user_id="missing-account-user",
            status="connected",
            connection_metadata={},
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_oauth_connections_enforce_provider_user_uniqueness() -> None:
    session, _ = _create_in_memory_schema()
    first_account = Account(
        id=uuid4(),
        username="oauth-owner-1",
        email="oauth-owner-1@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    second_account = Account(
        id=uuid4(),
        username="oauth-owner-2",
        email="oauth-owner-2@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add_all([first_account, second_account])
    session.commit()

    session.add(
        OAuthConnection(
            account_id=first_account.id,
            provider="discord",
            provider_user_id="discord-user-123",
            status="connected",
            connection_metadata={},
        )
    )
    session.commit()

    session.add(
        OAuthConnection(
            account_id=second_account.id,
            provider="discord",
            provider_user_id="discord-user-123",
            status="connected",
            connection_metadata={},
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_addresses_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        Address(
            account_id=uuid4(),
            address_type="billing",
            full_name="Missing Account",
            line1="100 Example Street",
            city_or_locality="Chicago",
            country_code="US",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_addresses_require_country_code() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="address-owner",
        email="address-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        Address(
            account_id=account.id,
            address_type="billing",
            full_name="Address Owner",
            line1="100 Example Street",
            city_or_locality="Chicago",
            country_code=None,  # type: ignore[arg-type]
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_tickets_require_existing_account() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        SupportTicket(
            account_id=uuid4(),
            ticket_code="SUP-2001",
            request_type="support",
            priority="high",
            subject="Missing account",
            description="This ticket should fail.",
            status="open",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_tickets_enforce_unique_ticket_code() -> None:
    session, _ = _create_in_memory_schema()
    first_account = Account(
        id=uuid4(),
        username="support-owner-1",
        email="support-owner-1@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    second_account = Account(
        id=uuid4(),
        username="support-owner-2",
        email="support-owner-2@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add_all([first_account, second_account])
    session.commit()

    session.add(
        SupportTicket(
            account_id=first_account.id,
            ticket_code="SUP-2002",
            request_type="support",
            priority="high",
            subject="First ticket",
            description="First description.",
            status="open",
        )
    )
    session.commit()

    session.add(
        SupportTicket(
            account_id=second_account.id,
            ticket_code="SUP-2002",
            request_type="support",
            priority="low",
            subject="Duplicate code",
            description="Second description.",
            status="open",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_ticket_messages_require_existing_ticket() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        SupportTicketMessage(
            ticket_id=uuid4(),
            author_type="account",
            message_body="This message should fail.",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_ticket_messages_require_message_body() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="support-message-owner",
        email="support-message-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    ticket = SupportTicket(
        id=uuid4(),
        account_id=account.id,
        ticket_code="SUP-2003",
        request_type="support",
        priority="normal",
        subject="Message body test",
        description="Base ticket for invalid message test.",
        status="open",
    )
    session.add_all([account, ticket])
    session.commit()

    session.add(
        SupportTicketMessage(
            ticket_id=ticket.id,
            account_id=account.id,
            author_type="account",
            message_body=None,  # type: ignore[arg-type]
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_ticket_attachments_require_existing_ticket() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="support-attachment-owner",
        email="support-attachment-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    session.add(account)
    session.commit()

    session.add(
        SupportTicketAttachment(
            ticket_id=uuid4(),
            uploaded_by_account_id=account.id,
            storage_key="support/missing-ticket/attachment-1",
            original_filename="missing-ticket.png",
            content_type="image/png",
            file_size_bytes=1024,
            scan_status="pending",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_ticket_attachments_require_existing_uploader() -> None:
    session, _ = _create_in_memory_schema()
    account = Account(
        id=uuid4(),
        username="support-attachment-ticket-owner",
        email="support-attachment-ticket-owner@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    ticket = SupportTicket(
        id=uuid4(),
        account_id=account.id,
        ticket_code="SUP-2004",
        request_type="support",
        priority="normal",
        subject="Attachment uploader test",
        description="Base ticket for invalid attachment uploader test.",
        status="open",
    )
    session.add_all([account, ticket])
    session.commit()

    session.add(
        SupportTicketAttachment(
            ticket_id=ticket.id,
            uploaded_by_account_id=uuid4(),
            storage_key="support/SUP-2004/attachment-1",
            original_filename="missing-uploader.png",
            content_type="image/png",
            file_size_bytes=2048,
            scan_status="pending",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_support_ticket_attachments_enforce_unique_storage_key() -> None:
    session, _ = _create_in_memory_schema()
    first_account = Account(
        id=uuid4(),
        username="support-attachment-owner-1",
        email="support-attachment-owner-1@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    second_account = Account(
        id=uuid4(),
        username="support-attachment-owner-2",
        email="support-attachment-owner-2@example.com",
        password_hash="hashed-password",
        status="active",
        role="member",
    )
    first_ticket = SupportTicket(
        id=uuid4(),
        account_id=first_account.id,
        ticket_code="SUP-2005",
        request_type="support",
        priority="normal",
        subject="First attachment",
        description="First attachment description.",
        status="open",
    )
    second_ticket = SupportTicket(
        id=uuid4(),
        account_id=second_account.id,
        ticket_code="SUP-2006",
        request_type="support",
        priority="normal",
        subject="Second attachment",
        description="Second attachment description.",
        status="open",
    )
    session.add_all([first_account, second_account, first_ticket, second_ticket])
    session.commit()

    session.add(
        SupportTicketAttachment(
            ticket_id=first_ticket.id,
            uploaded_by_account_id=first_account.id,
            storage_key="support/shared/attachment-1",
            original_filename="first.png",
            content_type="image/png",
            file_size_bytes=1024,
            scan_status="clean",
        )
    )
    session.commit()

    session.add(
        SupportTicketAttachment(
            ticket_id=second_ticket.id,
            uploaded_by_account_id=second_account.id,
            storage_key="support/shared/attachment-1",
            original_filename="second.png",
            content_type="image/png",
            file_size_bytes=2048,
            scan_status="pending",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_announcements_require_title() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        Announcement(
            scope="global",
            title=None,  # type: ignore[arg-type]
            body="Missing title should fail.",
            severity="info",
            published_at=datetime.now(UTC),
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_service_statuses_require_product_code() -> None:
    session, _ = _create_in_memory_schema()
    session.add(
        ServiceStatus(
            product_code=None,  # type: ignore[arg-type]
            status="degraded",
            message="Missing product code should fail.",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
