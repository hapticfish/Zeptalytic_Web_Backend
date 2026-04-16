"""Central model-registration path for SQLAlchemy metadata discovery."""

from importlib import import_module

from app.db.models.rewards import REWARD_MODEL_MODULES


MODEL_MODULES = (
    "app.db.models.addresses",
    "app.db.models.account_security_settings",
    "app.db.models.accounts",
    "app.db.models.announcements",
    "app.db.models.auth_events",
    "app.db.models.auth_sessions",
    "app.db.models.communication_preferences",
    "app.db.models.discord_connection_history",
    "app.db.models.email_verification_tokens",
    "app.db.models.entitlement_summaries",
    "app.db.models.mfa_recovery_codes",
    "app.db.models.oauth_connections",
    "app.db.models.password_reset_tokens",
    "app.db.models.payment_method_summaries",
    "app.db.models.payment_summaries",
    "app.db.models.product_access_states",
    "app.db.models.profile_preferences",
    "app.db.models.profiles",
    "app.db.models.service_statuses",
    "app.db.models.subscription_summaries",
    "app.db.models.support_ticket_attachments",
    "app.db.models.support_ticket_messages",
    "app.db.models.support_tickets",
) + REWARD_MODEL_MODULES


def import_models() -> None:
    """Import concrete model modules here as they are added."""
    for module_name in MODEL_MODULES:
        import_module(module_name)
