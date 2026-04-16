from importlib import import_module
from pathlib import Path

import app.db.models as model_registry
from app.db.models.account_security_settings import AccountSecuritySettings
from app.db.models.accounts import Account
from app.db.models.addresses import Address
from app.db.models.announcements import Announcement
from app.db.models.auth_events import AuthEvent
from app.db.models.auth_sessions import AuthSession
from app.db.models.communication_preferences import CommunicationPreference
from app.db.models.discord_connection_history import DiscordConnectionHistory
from app.db.models.email_verification_tokens import EmailVerificationToken
from app.db.models.entitlement_summaries import EntitlementSummary
from app.db.models.mfa_recovery_codes import MfaRecoveryCode
from app.db.models.oauth_connections import OAuthConnection
from app.db.models.password_reset_tokens import PasswordResetToken
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.product_access_states import ProductAccessState
from app.db.models.profile_preferences import ProfilePreference
from app.db.models.profiles import Profile
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_events import RewardEvent
from app.db.models.rewards.reward_milestones import RewardMilestone
from app.db.models.rewards.reward_tier_definitions import RewardTierDefinition
from app.db.models.service_statuses import ServiceStatus
from app.db.models.subscription_summaries import SubscriptionSummary
from app.db.models.support_ticket_attachments import SupportTicketAttachment
from app.db.models.support_ticket_messages import SupportTicketMessage
from app.db.models.support_tickets import SupportTicket


EXPECTED_MODEL_FILES = {
    "accounts.py",
    "account_security_settings.py",
    "addresses.py",
    "announcements.py",
    "auth_events.py",
    "auth_sessions.py",
    "communication_preferences.py",
    "discord_connection_history.py",
    "email_verification_tokens.py",
    "entitlement_summaries.py",
    "mfa_recovery_codes.py",
    "oauth_connections.py",
    "password_reset_tokens.py",
    "payment_method_summaries.py",
    "payment_summaries.py",
    "product_access_states.py",
    "profile_preferences.py",
    "profiles.py",
    "service_statuses.py",
    "subscription_summaries.py",
    "support_ticket_attachments.py",
    "support_ticket_messages.py",
    "support_tickets.py",
    "testimonials.py",
}

EXPECTED_REWARD_MODEL_FILES = {
    "__init__.py",
    "reward_accounts.py",
    "reward_events.py",
    "reward_milestones.py",
    "reward_tier_definitions.py",
}

EXPECTED_MODEL_MODULES = {
    "app.db.models.accounts": Account,
    "app.db.models.account_security_settings": AccountSecuritySettings,
    "app.db.models.addresses": Address,
    "app.db.models.announcements": Announcement,
    "app.db.models.auth_events": AuthEvent,
    "app.db.models.auth_sessions": AuthSession,
    "app.db.models.communication_preferences": CommunicationPreference,
    "app.db.models.discord_connection_history": DiscordConnectionHistory,
    "app.db.models.email_verification_tokens": EmailVerificationToken,
    "app.db.models.entitlement_summaries": EntitlementSummary,
    "app.db.models.mfa_recovery_codes": MfaRecoveryCode,
    "app.db.models.oauth_connections": OAuthConnection,
    "app.db.models.password_reset_tokens": PasswordResetToken,
    "app.db.models.payment_method_summaries": PaymentMethodSummary,
    "app.db.models.payment_summaries": PaymentSummary,
    "app.db.models.product_access_states": ProductAccessState,
    "app.db.models.profile_preferences": ProfilePreference,
    "app.db.models.profiles": Profile,
    "app.db.models.rewards.reward_accounts": RewardAccount,
    "app.db.models.rewards.reward_events": RewardEvent,
    "app.db.models.rewards.reward_milestones": RewardMilestone,
    "app.db.models.rewards.reward_tier_definitions": RewardTierDefinition,
    "app.db.models.service_statuses": ServiceStatus,
    "app.db.models.subscription_summaries": SubscriptionSummary,
    "app.db.models.support_ticket_attachments": SupportTicketAttachment,
    "app.db.models.support_ticket_messages": SupportTicketMessage,
    "app.db.models.support_tickets": SupportTicket,
}


def test_expected_model_files_exist() -> None:
    models_dir = Path(__file__).resolve().parents[2] / "app" / "db" / "models"
    model_files = {path.name for path in models_dir.glob("*.py")}

    assert EXPECTED_MODEL_FILES.issubset(model_files)


def test_expected_rewards_model_files_exist() -> None:
    rewards_dir = Path(__file__).resolve().parents[2] / "app" / "db" / "models" / "rewards"
    reward_model_files = {path.name for path in rewards_dir.glob("*.py")}

    assert EXPECTED_REWARD_MODEL_FILES == reward_model_files


def test_expected_model_modules_are_registered_and_importable() -> None:
    assert set(EXPECTED_MODEL_MODULES).issubset(set(model_registry.MODEL_MODULES))
    assert "app.db.models.auth" not in model_registry.MODEL_MODULES

    for module_name in EXPECTED_MODEL_MODULES:
        import_module(module_name)


def test_models_live_in_expected_modules() -> None:
    for module_name, model_class in EXPECTED_MODEL_MODULES.items():
        assert model_class.__module__ == module_name
