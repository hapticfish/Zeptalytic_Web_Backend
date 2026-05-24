from app.core.config import Settings
from app.schemas.email import (
    EmailSenderProfileKey,
    EmailTemplateKey,
    FUTURE_SCOPE_TEMPLATE_KEYS,
    PHASE_ONE_TRIGGER_TEMPLATE_KEYS,
    build_email_sender_profiles,
    build_email_template_catalog,
    resolve_email_sender_profile,
)


def _build_settings() -> Settings:
    return Settings(
        email_from_address="hello@example.com",
        email_from_name="Example Hello",
        email_reply_to_address="support@example.com",
        email_support_from_address="support@example.com",
        email_billing_from_address="billing@example.com",
        email_alerts_from_address="alerts@example.com",
        email_updates_from_address="updates@example.com",
        brevo_template_welcome_id=101,
        brevo_template_support_response_id=102,
        brevo_template_order_confirmation_id=103,
        brevo_template_news_updates_id=104,
        brevo_template_failed_signup_id=105,
        brevo_template_email_changed_id=106,
        brevo_template_password_reset_id=107,
        brevo_template_account_details_changed_id=108,
        brevo_template_email_verification_id=109,
        brevo_template_payment_failed_id=110,
        brevo_template_subscription_expiring_id=111,
    )


def test_email_template_catalog_represents_all_brevo_templates() -> None:
    settings = _build_settings()

    catalog = build_email_template_catalog(settings)

    assert set(catalog) == set(EmailTemplateKey)
    assert catalog[EmailTemplateKey.WELCOME].provider_template_id == 101
    assert catalog[EmailTemplateKey.SUPPORT_RESPONSE].provider_template_id == 102
    assert catalog[EmailTemplateKey.ORDER_CONFIRMATION].provider_template_id == 103
    assert catalog[EmailTemplateKey.NEWS_UPDATES].provider_template_id == 104
    assert catalog[EmailTemplateKey.FAILED_SIGNUP].provider_template_id == 105
    assert catalog[EmailTemplateKey.EMAIL_CHANGED].provider_template_id == 106
    assert catalog[EmailTemplateKey.PASSWORD_RESET].provider_template_id == 107
    assert catalog[EmailTemplateKey.ACCOUNT_DETAILS_CHANGED].provider_template_id == 108
    assert catalog[EmailTemplateKey.EMAIL_VERIFICATION].provider_template_id == 109
    assert catalog[EmailTemplateKey.PAYMENT_FAILED].provider_template_id == 110
    assert catalog[EmailTemplateKey.SUBSCRIPTION_EXPIRING].provider_template_id == 111


def test_email_sender_profile_resolver_matches_sender_matrix() -> None:
    settings = _build_settings()

    profiles = build_email_sender_profiles(settings)

    assert profiles[EmailSenderProfileKey.HELLO].from_name == "Example Hello"
    assert profiles[EmailSenderProfileKey.HELLO].from_email == "hello@example.com"
    assert profiles[EmailSenderProfileKey.HELLO].reply_to_email == "support@example.com"
    assert profiles[EmailSenderProfileKey.SUPPORT].from_name == "Zeptalytic Support"
    assert profiles[EmailSenderProfileKey.SUPPORT].from_email == "support@example.com"
    assert profiles[EmailSenderProfileKey.SUPPORT].reply_to_email == "support@example.com"
    assert profiles[EmailSenderProfileKey.BILLING].from_name == "Zeptalytic Billing"
    assert profiles[EmailSenderProfileKey.BILLING].from_email == "billing@example.com"
    assert profiles[EmailSenderProfileKey.BILLING].reply_to_email == "billing@example.com"
    assert profiles[EmailSenderProfileKey.ALERTS].from_name == "Zeptalytic Alerts"
    assert profiles[EmailSenderProfileKey.ALERTS].from_email == "alerts@example.com"
    assert profiles[EmailSenderProfileKey.ALERTS].reply_to_email == "support@example.com"
    assert profiles[EmailSenderProfileKey.UPDATES].from_name == "Zeptalytic Updates"
    assert profiles[EmailSenderProfileKey.UPDATES].from_email == "updates@example.com"
    assert profiles[EmailSenderProfileKey.UPDATES].reply_to_email == "support@example.com"

    assert resolve_email_sender_profile(EmailTemplateKey.EMAIL_VERIFICATION, settings).key == (
        EmailSenderProfileKey.SUPPORT
    )
    assert resolve_email_sender_profile(EmailTemplateKey.WELCOME, settings).key == (
        EmailSenderProfileKey.HELLO
    )
    assert resolve_email_sender_profile(EmailTemplateKey.ORDER_CONFIRMATION, settings).key == (
        EmailSenderProfileKey.BILLING
    )
    assert resolve_email_sender_profile(EmailTemplateKey.NEWS_UPDATES, settings).key == (
        EmailSenderProfileKey.UPDATES
    )


def test_email_catalog_uses_reply_capable_senders_and_flags_future_scope_templates() -> None:
    settings = _build_settings()

    catalog = build_email_template_catalog(settings)
    profiles = build_email_sender_profiles(settings)

    assert PHASE_ONE_TRIGGER_TEMPLATE_KEYS == {
        EmailTemplateKey.WELCOME,
        EmailTemplateKey.PASSWORD_RESET,
        EmailTemplateKey.ACCOUNT_DETAILS_CHANGED,
        EmailTemplateKey.EMAIL_VERIFICATION,
    }
    assert FUTURE_SCOPE_TEMPLATE_KEYS == {
        EmailTemplateKey.SUPPORT_RESPONSE,
        EmailTemplateKey.ORDER_CONFIRMATION,
        EmailTemplateKey.NEWS_UPDATES,
        EmailTemplateKey.FAILED_SIGNUP,
        EmailTemplateKey.EMAIL_CHANGED,
        EmailTemplateKey.PAYMENT_FAILED,
        EmailTemplateKey.SUBSCRIPTION_EXPIRING,
    }

    for template_key, entry in catalog.items():
        profile = profiles[entry.sender_profile_key]
        assert "no-reply@" not in profile.from_email
        assert "no-reply@" not in profile.reply_to_email
        assert entry.phase_one_trigger_enabled == (template_key in PHASE_ONE_TRIGGER_TEMPLATE_KEYS)
