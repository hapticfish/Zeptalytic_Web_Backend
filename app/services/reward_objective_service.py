from __future__ import annotations

from uuid import UUID

from app.db.repositories.reward_objective_repository import RewardObjectiveRepository
from app.schemas.reward_objectives import (
    RewardObjectiveGroup,
    RewardObjectiveItem,
    RewardObjectiveMilestone,
    RewardObjectiveProgress,
    RewardObjectiveReward,
    RewardObjectivesResponse,
)


class RewardObjectivesNotFoundError(Exception):
    """Raised when the requested account does not exist."""


class RewardObjectiveService:
    def __init__(self, repository: RewardObjectiveRepository) -> None:
        self._repository = repository

    def get_objectives(self, account_id: UUID) -> RewardObjectivesResponse:
        objective_groups = self._repository.get_account_objectives(account_id)
        if objective_groups is None:
            raise RewardObjectivesNotFoundError(f"No account exists for {account_id}")

        return RewardObjectivesResponse(
            account_id=objective_groups.account_id,
            groups=[
                RewardObjectiveGroup(
                    group_code=group.group_code,
                    objectives=[
                        RewardObjectiveItem(
                            objective_definition_id=objective.objective_definition_id,
                            objective_code=objective.objective_code,
                            title=objective.title,
                            description=objective.description,
                            scope_type=objective.scope_type,
                            product_code=objective.product_code,
                            objective_type=objective.objective_type,
                            is_repeatable=objective.is_repeatable,
                            repeat_group_key=objective.repeat_group_key,
                            tier_gate=objective.tier_gate,
                            subscription_gate_product_code=objective.subscription_gate_product_code,
                            subscription_gate_plan_code=objective.subscription_gate_plan_code,
                            is_milestone_objective=objective.is_milestone_objective,
                            sort_group=objective.sort_group,
                            sort_order=objective.sort_order,
                            metadata=objective.metadata,
                            progress=RewardObjectiveProgress(
                                current_count=objective.progress.current_count,
                                completed_count=objective.progress.completed_count,
                                required_count=objective.progress.required_count,
                                status=objective.progress.status,
                                repeat_iteration=objective.progress.repeat_iteration,
                                last_completed_at=objective.progress.last_completed_at,
                                last_progress_at=objective.progress.last_progress_at,
                                metadata=objective.progress.metadata,
                            ),
                            rewards=[
                                RewardObjectiveReward(
                                    reward_code=reward.reward_code,
                                    reward_type=reward.reward_type,
                                    display_name=reward.display_name,
                                    description=reward.description,
                                    grant_order=reward.grant_order,
                                )
                                for reward in objective.rewards
                            ],
                            linked_milestone=(
                                RewardObjectiveMilestone(
                                    milestone_points=objective.linked_milestone.milestone_points,
                                    tier_code=objective.linked_milestone.tier_code,
                                    is_tier_boundary=objective.linked_milestone.is_tier_boundary,
                                )
                                if objective.linked_milestone is not None
                                else None
                            ),
                        )
                        for objective in group.objectives
                    ],
                )
                for group in objective_groups.groups
            ],
        )
