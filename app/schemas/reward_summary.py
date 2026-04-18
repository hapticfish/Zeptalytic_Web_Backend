from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RewardSummaryPerk(BaseModel):
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    granted_at: datetime


class RewardSummaryBadge(BaseModel):
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None
    earned_at: datetime


class RewardSummaryNextMilestone(BaseModel):
    milestone_points: int
    points_remaining: int
    tier_code: str
    is_tier_boundary: bool


class RewardSummaryResponse(BaseModel):
    account_id: UUID
    current_points: int
    current_tier: str
    current_tier_progress_points: int
    current_tier_band_max_points: int = 1000
    next_milestone: RewardSummaryNextMilestone | None
    active_perks: list[RewardSummaryPerk]
    earned_badges: list[RewardSummaryBadge]
