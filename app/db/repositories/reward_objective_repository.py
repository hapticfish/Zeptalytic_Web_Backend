from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.rewards.account_objective_progress import AccountObjectiveProgress
from app.db.models.rewards.objective_definitions import ObjectiveDefinition
from app.db.models.rewards.objective_reward_links import ObjectiveRewardLink
from app.db.models.rewards.reward_definitions import RewardDefinition
from app.db.models.rewards.reward_milestones import RewardMilestone


@dataclass(slots=True)
class RewardObjectiveRewardRecord:
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    grant_order: int


@dataclass(slots=True)
class RewardObjectiveMilestoneRecord:
    milestone_points: int
    tier_code: str
    is_tier_boundary: bool


@dataclass(slots=True)
class RewardObjectiveProgressRecord:
    current_count: int
    completed_count: int
    required_count: int
    status: str
    repeat_iteration: int | None
    last_completed_at: datetime | None
    last_progress_at: datetime | None
    metadata: dict[str, object]


@dataclass(slots=True)
class RewardObjectiveRecord:
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
    progress: RewardObjectiveProgressRecord
    rewards: list[RewardObjectiveRewardRecord]
    linked_milestone: RewardObjectiveMilestoneRecord | None


@dataclass(slots=True)
class RewardObjectiveGroupRecord:
    group_code: str
    objectives: list[RewardObjectiveRecord]


@dataclass(slots=True)
class RewardObjectivesRecord:
    account_id: UUID
    groups: list[RewardObjectiveGroupRecord]


class RewardObjectiveRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_account_objectives(self, account_id: UUID) -> RewardObjectivesRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        objective_definitions = self._db.scalars(
            select(ObjectiveDefinition)
            .where(ObjectiveDefinition.active.is_(True))
            .order_by(ObjectiveDefinition.sort_group.asc(), ObjectiveDefinition.sort_order.asc())
        ).all()

        progress_by_objective_id = {
            progress.objective_definition_id: progress
            for progress in self._db.scalars(
                select(AccountObjectiveProgress).where(
                    AccountObjectiveProgress.account_id == account_id
                )
            ).all()
        }

        rewards_by_objective_id: dict[UUID, list[RewardObjectiveRewardRecord]] = {}
        for link, reward_definition in self._db.execute(
            select(ObjectiveRewardLink, RewardDefinition)
            .join(
                RewardDefinition,
                RewardDefinition.id == ObjectiveRewardLink.reward_definition_id,
            )
            .order_by(
                ObjectiveRewardLink.objective_definition_id.asc(),
                ObjectiveRewardLink.grant_order.asc(),
                RewardDefinition.display_name.asc(),
            )
        ).all():
            rewards_by_objective_id.setdefault(link.objective_definition_id, []).append(
                RewardObjectiveRewardRecord(
                    reward_code=reward_definition.reward_code,
                    reward_type=reward_definition.reward_type,
                    display_name=reward_definition.display_name,
                    description=reward_definition.description,
                    grant_order=link.grant_order,
                )
            )

        milestones_by_objective_id = {
            milestone.linked_objective_definition_id: RewardObjectiveMilestoneRecord(
                milestone_points=milestone.milestone_points,
                tier_code=milestone.tier_code,
                is_tier_boundary=milestone.is_tier_boundary,
            )
            for milestone in self._db.scalars(
                select(RewardMilestone).where(RewardMilestone.linked_objective_definition_id.is_not(None))
            ).all()
            if milestone.linked_objective_definition_id is not None
        }

        groups: list[RewardObjectiveGroupRecord] = []
        current_group: RewardObjectiveGroupRecord | None = None
        for objective_definition in objective_definitions:
            if current_group is None or current_group.group_code != objective_definition.sort_group:
                current_group = RewardObjectiveGroupRecord(
                    group_code=objective_definition.sort_group,
                    objectives=[],
                )
                groups.append(current_group)

            progress = progress_by_objective_id.get(objective_definition.id)
            current_group.objectives.append(
                RewardObjectiveRecord(
                    objective_definition_id=objective_definition.id,
                    objective_code=objective_definition.objective_code,
                    title=objective_definition.title,
                    description=objective_definition.description,
                    scope_type=objective_definition.scope_type,
                    product_code=objective_definition.product_code,
                    objective_type=objective_definition.objective_type,
                    is_repeatable=objective_definition.is_repeatable,
                    repeat_group_key=objective_definition.repeat_group_key,
                    tier_gate=objective_definition.tier_gate,
                    subscription_gate_product_code=objective_definition.subscription_gate_product_code,
                    subscription_gate_plan_code=objective_definition.subscription_gate_plan_code,
                    is_milestone_objective=objective_definition.is_milestone_objective,
                    sort_group=objective_definition.sort_group,
                    sort_order=objective_definition.sort_order,
                    metadata=objective_definition.objective_metadata,
                    progress=RewardObjectiveProgressRecord(
                        current_count=progress.current_count if progress is not None else 0,
                        completed_count=progress.completed_count if progress is not None else 0,
                        required_count=objective_definition.required_count,
                        status=progress.status if progress is not None else "not_started",
                        repeat_iteration=progress.repeat_iteration if progress is not None else None,
                        last_completed_at=(
                            progress.last_completed_at if progress is not None else None
                        ),
                        last_progress_at=progress.last_progress_at if progress is not None else None,
                        metadata=progress.progress_metadata if progress is not None else {},
                    ),
                    rewards=rewards_by_objective_id.get(objective_definition.id, []),
                    linked_milestone=milestones_by_objective_id.get(objective_definition.id),
                )
            )

        return RewardObjectivesRecord(account_id=account_id, groups=groups)
