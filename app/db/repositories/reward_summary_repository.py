from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.rewards.account_badges import AccountBadge
from app.db.models.rewards.badge_definitions import BadgeDefinition
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_definitions import RewardDefinition
from app.db.models.rewards.reward_grants import RewardGrant
from app.db.models.rewards.reward_milestones import RewardMilestone


@dataclass(slots=True)
class RewardSummaryPerkRecord:
    reward_code: str
    reward_type: str
    display_name: str
    description: str
    granted_at: datetime


@dataclass(slots=True)
class RewardSummaryBadgeRecord:
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None
    earned_at: datetime


@dataclass(slots=True)
class RewardSummaryMilestoneRecord:
    milestone_points: int
    tier_code: str
    is_tier_boundary: bool


@dataclass(slots=True)
class RewardSummaryRecord:
    account_id: UUID
    current_points: int
    current_tier: str
    current_tier_progress_points: int
    next_milestone: RewardSummaryMilestoneRecord | None
    active_perks: list[RewardSummaryPerkRecord]
    earned_badges: list[RewardSummaryBadgeRecord]


class RewardSummaryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_account_summary(self, account_id: UUID) -> RewardSummaryRecord | None:
        reward_account = self._db.get(RewardAccount, account_id)
        if reward_account is None:
            return None

        next_milestone_model = self._db.scalar(
            select(RewardMilestone)
            .where(RewardMilestone.milestone_points == reward_account.next_milestone_points)
            .order_by(RewardMilestone.sort_order)
        )
        if next_milestone_model is None:
            next_milestone_model = self._db.scalar(
                select(RewardMilestone)
                .where(RewardMilestone.milestone_points >= reward_account.current_points)
                .order_by(RewardMilestone.sort_order)
            )

        active_perks = [
            RewardSummaryPerkRecord(
                reward_code=reward_definition.reward_code,
                reward_type=reward_definition.reward_type,
                display_name=reward_definition.display_name,
                description=reward_definition.description,
                granted_at=reward_grant.granted_at,
            )
            for reward_grant, reward_definition in self._db.execute(
                select(RewardGrant, RewardDefinition)
                .join(
                    RewardDefinition,
                    RewardDefinition.id == RewardGrant.reward_definition_id,
                )
                .where(
                    RewardGrant.account_id == account_id,
                    RewardGrant.status == "granted",
                    RewardGrant.revoked_at.is_(None),
                )
                .order_by(RewardGrant.granted_at.desc(), RewardDefinition.display_name.asc())
            ).all()
        ]

        earned_badges = [
            RewardSummaryBadgeRecord(
                badge_code=badge_definition.badge_code,
                display_name=badge_definition.display_name,
                description=badge_definition.description,
                icon_ref=badge_definition.icon_ref,
                earned_at=account_badge.earned_at,
            )
            for account_badge, badge_definition in self._db.execute(
                select(AccountBadge, BadgeDefinition)
                .join(
                    BadgeDefinition,
                    BadgeDefinition.id == AccountBadge.badge_definition_id,
                )
                .where(
                    AccountBadge.account_id == account_id,
                    AccountBadge.revoked_at.is_(None),
                )
                .order_by(AccountBadge.earned_at.desc(), BadgeDefinition.display_name.asc())
            ).all()
        ]

        next_milestone = None
        if next_milestone_model is not None:
            next_milestone = RewardSummaryMilestoneRecord(
                milestone_points=next_milestone_model.milestone_points,
                tier_code=next_milestone_model.tier_code,
                is_tier_boundary=next_milestone_model.is_tier_boundary,
            )

        return RewardSummaryRecord(
            account_id=reward_account.account_id,
            current_points=reward_account.current_points,
            current_tier=reward_account.current_tier,
            current_tier_progress_points=reward_account.current_tier_progress_points,
            next_milestone=next_milestone,
            active_perks=active_perks,
            earned_badges=earned_badges,
        )
