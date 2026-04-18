from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RewardObjectiveReward(BaseModel):
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    grant_order: int


class RewardObjectiveMilestone(BaseModel):
    milestone_points: int
    tier_code: str
    is_tier_boundary: bool


class RewardObjectiveProgress(BaseModel):
    current_count: int
    completed_count: int
    required_count: int
    status: str
    repeat_iteration: int | None
    last_completed_at: datetime | None
    last_progress_at: datetime | None
    metadata: dict[str, object]


class RewardObjectiveItem(BaseModel):
    objective_definition_id: UUID
    objective_code: str
    title: str
    description: str
    scope_type: str
    product_code: str | None
    objective_type: str
    is_repeatable: bool
    repeat_group_key: str | None
    tier_gate: str | None
    subscription_gate_product_code: str | None
    subscription_gate_plan_code: str | None
    is_milestone_objective: bool
    sort_group: str
    sort_order: int
    metadata: dict[str, object]
    progress: RewardObjectiveProgress
    rewards: list[RewardObjectiveReward]
    linked_milestone: RewardObjectiveMilestone | None


class RewardObjectiveGroup(BaseModel):
    group_code: str
    objectives: list[RewardObjectiveItem]


class RewardObjectivesResponse(BaseModel):
    account_id: UUID
    groups: list[RewardObjectiveGroup]
