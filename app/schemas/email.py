from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from app.core.config import Settings, settings


class EmailTemplateKey(StrEnum):
    WELCOME = "welcome"
    SUPPORT_RESPONSE = "support_response"
    ORDER_CONFIRMATION = "order_confirmation"
    NEWS_UPDATES = "news_updates"
    FAILED_SIGNUP = "failed_signup"
    EMAIL_CHANGED = "email_changed"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_DETAILS_CHANGED = "account_details_changed"
    EMAIL_VERIFICATION = "email_verification"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"


class EmailSenderProfileKey(StrEnum):
    HELLO = "hello"
    SUPPORT = "support"
    BILLING = "billing"
    ALERTS = "alerts"
    UPDATES = "updates"


@dataclass(frozen=True, slots=True)
class ResolvedEmailSenderProfile:
    key: EmailSenderProfileKey
    from_name: str
    from_email: str
    reply_to_name: str
    reply_to_email: str


@dataclass(frozen=True, slots=True)
class EmailTemplateCatalogEntry:
    key: EmailTemplateKey
    provider_template_id: int
    sender_profile_key: EmailSenderProfileKey
    phase_one_trigger_enabled: bool


class EmailWebhookIngestResponse(BaseModel):
    status: Literal["ok", "duplicate"]


class EmailWebhookErrorResponse(BaseModel):
    status: Literal["error"]


PHASE_ONE_TRIGGER_TEMPLATE_KEYS: frozenset[EmailTemplateKey] = frozenset(
    {
        EmailTemplateKey.WELCOME,
        EmailTemplateKey.PASSWORD_RESET,
        EmailTemplateKey.ACCOUNT_DETAILS_CHANGED,
        EmailTemplateKey.EMAIL_VERIFICATION,
    }
)

FUTURE_SCOPE_TEMPLATE_KEYS: frozenset[EmailTemplateKey] = frozenset(
    set(EmailTemplateKey) - set(PHASE_ONE_TRIGGER_TEMPLATE_KEYS)
)


def build_email_sender_profiles(
    app_settings: Settings | None = None,
) -> dict[EmailSenderProfileKey, ResolvedEmailSenderProfile]:
    active_settings = app_settings or settings

    return {
        EmailSenderProfileKey.HELLO: ResolvedEmailSenderProfile(
            key=EmailSenderProfileKey.HELLO,
            from_name=active_settings.email_from_name,
            from_email=active_settings.email_from_address,
            reply_to_name="Zeptalytic Support",
            reply_to_email=active_settings.email_reply_to_address,
        ),
        EmailSenderProfileKey.SUPPORT: ResolvedEmailSenderProfile(
            key=EmailSenderProfileKey.SUPPORT,
            from_name="Zeptalytic Support",
            from_email=active_settings.email_support_from_address,
            reply_to_name="Zeptalytic Support",
            reply_to_email=active_settings.email_support_from_address,
        ),
        EmailSenderProfileKey.BILLING: ResolvedEmailSenderProfile(
            key=EmailSenderProfileKey.BILLING,
            from_name="Zeptalytic Billing",
            from_email=active_settings.email_billing_from_address,
            reply_to_name="Zeptalytic Billing",
            reply_to_email=active_settings.email_billing_from_address,
        ),
        EmailSenderProfileKey.ALERTS: ResolvedEmailSenderProfile(
            key=EmailSenderProfileKey.ALERTS,
            from_name="Zeptalytic Alerts",
            from_email=active_settings.email_alerts_from_address,
            reply_to_name="Zeptalytic Support",
            reply_to_email=active_settings.email_reply_to_address,
        ),
        EmailSenderProfileKey.UPDATES: ResolvedEmailSenderProfile(
            key=EmailSenderProfileKey.UPDATES,
            from_name="Zeptalytic Updates",
            from_email=active_settings.email_updates_from_address,
            reply_to_name="Zeptalytic Support",
            reply_to_email=active_settings.email_reply_to_address,
        ),
    }


def build_email_template_catalog(
    app_settings: Settings | None = None,
) -> dict[EmailTemplateKey, EmailTemplateCatalogEntry]:
    active_settings = app_settings or settings

    return {
        EmailTemplateKey.WELCOME: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.WELCOME,
            provider_template_id=active_settings.brevo_template_welcome_id,
            sender_profile_key=EmailSenderProfileKey.HELLO,
            phase_one_trigger_enabled=True,
        ),
        EmailTemplateKey.SUPPORT_RESPONSE: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.SUPPORT_RESPONSE,
            provider_template_id=active_settings.brevo_template_support_response_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.ORDER_CONFIRMATION: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.ORDER_CONFIRMATION,
            provider_template_id=active_settings.brevo_template_order_confirmation_id,
            sender_profile_key=EmailSenderProfileKey.BILLING,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.NEWS_UPDATES: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.NEWS_UPDATES,
            provider_template_id=active_settings.brevo_template_news_updates_id,
            sender_profile_key=EmailSenderProfileKey.UPDATES,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.FAILED_SIGNUP: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.FAILED_SIGNUP,
            provider_template_id=active_settings.brevo_template_failed_signup_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.EMAIL_CHANGED: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.EMAIL_CHANGED,
            provider_template_id=active_settings.brevo_template_email_changed_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.PASSWORD_RESET: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.PASSWORD_RESET,
            provider_template_id=active_settings.brevo_template_password_reset_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=True,
        ),
        EmailTemplateKey.ACCOUNT_DETAILS_CHANGED: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.ACCOUNT_DETAILS_CHANGED,
            provider_template_id=active_settings.brevo_template_account_details_changed_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=True,
        ),
        EmailTemplateKey.EMAIL_VERIFICATION: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.EMAIL_VERIFICATION,
            provider_template_id=active_settings.brevo_template_email_verification_id,
            sender_profile_key=EmailSenderProfileKey.SUPPORT,
            phase_one_trigger_enabled=True,
        ),
        EmailTemplateKey.PAYMENT_FAILED: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.PAYMENT_FAILED,
            provider_template_id=active_settings.brevo_template_payment_failed_id,
            sender_profile_key=EmailSenderProfileKey.BILLING,
            phase_one_trigger_enabled=False,
        ),
        EmailTemplateKey.SUBSCRIPTION_EXPIRING: EmailTemplateCatalogEntry(
            key=EmailTemplateKey.SUBSCRIPTION_EXPIRING,
            provider_template_id=active_settings.brevo_template_subscription_expiring_id,
            sender_profile_key=EmailSenderProfileKey.BILLING,
            phase_one_trigger_enabled=False,
        ),
    }


def resolve_email_sender_profile(
    template_key: EmailTemplateKey,
    app_settings: Settings | None = None,
) -> ResolvedEmailSenderProfile:
    active_settings = app_settings or settings
    catalog_entry = build_email_template_catalog(active_settings)[template_key]
    return build_email_sender_profiles(active_settings)[catalog_entry.sender_profile_key]
