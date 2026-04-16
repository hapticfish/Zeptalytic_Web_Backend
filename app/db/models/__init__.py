"""Central model-registration path for SQLAlchemy metadata discovery."""

from importlib import import_module


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
    "app.db.models.rewards.account_badges",
    "app.db.models.rewards.reward_accounts",
    "app.db.models.rewards.account_objective_progress",
    "app.db.models.rewards.badge_definitions",
    "app.db.models.rewards.objective_definitions",
    "app.db.models.rewards.objective_reward_links",
    "app.db.models.rewards.reward_definitions",
    "app.db.models.rewards.reward_events",
    "app.db.models.rewards.reward_grants",
    "app.db.models.rewards.reward_milestones",
    "app.db.models.rewards.reward_tier_definitions",
    "app.db.models.service_statuses",
    "app.db.models.subscription_summaries",
    "app.db.models.support_ticket_attachments",
    "app.db.models.support_ticket_messages",
    "app.db.models.support_tickets",
)


def import_models() -> None:
    """Import concrete model modules here as they are added."""
    for module_name in MODEL_MODULES:
        import_module(module_name)
