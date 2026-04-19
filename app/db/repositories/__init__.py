"""Database repository layer."""

from app.db.repositories.address_repository import AddressRepository
from app.db.repositories.auth_repository import AuthRepository
from app.db.repositories.communication_preference_repository import (
    CommunicationPreferenceRepository,
)
from app.db.repositories.profile_settings_repository import ProfileSettingsRepository
from app.db.repositories.reward_notification_repository import RewardNotificationRepository
from app.db.repositories.reward_objective_repository import RewardObjectiveRepository
from app.db.repositories.reward_progression_repository import RewardProgressionRepository
from app.db.repositories.reward_summary_repository import RewardSummaryRepository

__all__ = [
    "AddressRepository",
    "AuthRepository",
    "CommunicationPreferenceRepository",
    "ProfileSettingsRepository",
    "RewardNotificationRepository",
    "RewardObjectiveRepository",
    "RewardProgressionRepository",
    "RewardSummaryRepository",
]
