from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.accounts import Account
from app.db.models.rewards.account_badges import AccountBadge
from app.db.models.rewards.account_objective_progress import AccountObjectiveProgress
from app.db.models.rewards.objective_definitions import ObjectiveDefinition
from app.db.models.rewards.reward_accounts import RewardAccount
from app.db.models.rewards.reward_events import RewardEvent
from app.db.models.rewards.reward_grants import RewardGrant
from app.db.models.rewards.reward_notifications import RewardNotification

_MAX_MILESTONE_POINTS = 5000


@dataclass(slots=True)
class RewardAccountSnapshotRecord:
    account_id: UUID
    current_points: int
    current_tier: str
    current_tier_progress_points: int
    next_milestone_points: int
    last_recomputed_at: datetime


@dataclass(slots=True)
class RewardEventApplicationRecord:
    event_id: UUID
    account_id: UUID
    event_type: str
    points_delta: int
    is_reversal: bool
    reversed_event_id: UUID | None
    status: str
    source_type: str
    source_reference: str | None
    created_at: datetime
    metadata: dict[str, object]
    reward_account: RewardAccountSnapshotRecord
    revoked_reward_grant_ids: list[UUID]
    revoked_badge_ids: list[UUID]


@dataclass(slots=True)
class ObjectiveProgressUpdateRecord:
    account_id: UUID
    objective_definition_id: UUID
    objective_code: str
    required_count: int
    current_count: int
    completed_count: int
    repeat_iteration: int | None
    status: str
    last_completed_at: datetime | None
    last_progress_at: datetime
    metadata: dict[str, object]
    completed_now: bool


@dataclass(slots=True)
class RewardNotificationQueueRecord:
    notification_id: UUID
    account_id: UUID
    notification_type: str
    status: str
    sequence_order: int
    queued_at: datetime
    metadata: dict[str, object]


class RewardProgressionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def award_points(
        self,
        *,
        account_id: UUID,
        event_type: str,
        points_delta: int,
        source_type: str,
        source_reference: str | None,
        status: str,
        created_at: datetime,
        metadata: dict[str, object],
        objective_definition_id: UUID | None = None,
        reward_definition_id: UUID | None = None,
        badge_definition_id: UUID | None = None,
    ) -> RewardEventApplicationRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        reward_event = RewardEvent(
            account_id=account_id,
            event_type=event_type,
            points_delta=points_delta,
            objective_definition_id=objective_definition_id,
            reward_definition_id=reward_definition_id,
            badge_definition_id=badge_definition_id,
            source_type=source_type,
            source_reference=source_reference,
            is_reversal=False,
            status=status,
            event_metadata=metadata,
            created_at=created_at,
        )
        self._db.add(reward_event)
        self._db.flush()

        reward_account = self._recompute_reward_account(account_id, recomputed_at=created_at)
        self._db.commit()

        return RewardEventApplicationRecord(
            event_id=reward_event.id,
            account_id=account_id,
            event_type=reward_event.event_type,
            points_delta=reward_event.points_delta,
            is_reversal=reward_event.is_reversal,
            reversed_event_id=reward_event.reversed_event_id,
            status=reward_event.status,
            source_type=reward_event.source_type,
            source_reference=reward_event.source_reference,
            created_at=reward_event.created_at,
            metadata=reward_event.event_metadata,
            reward_account=reward_account,
            revoked_reward_grant_ids=[],
            revoked_badge_ids=[],
        )

    def reverse_event(
        self,
        *,
        account_id: UUID,
        reversed_event_id: UUID,
        event_type: str,
        source_type: str,
        source_reference: str | None,
        status: str,
        created_at: datetime,
        metadata: dict[str, object],
        revocation_reason: str | None,
        points_delta: int | None = None,
    ) -> RewardEventApplicationRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        reversed_event = self._db.scalar(
            select(RewardEvent).where(
                RewardEvent.id == reversed_event_id,
                RewardEvent.account_id == account_id,
            )
        )
        if reversed_event is None:
            return None

        reversal_event = RewardEvent(
            account_id=account_id,
            event_type=event_type,
            points_delta=-reversed_event.points_delta if points_delta is None else points_delta,
            objective_definition_id=reversed_event.objective_definition_id,
            reward_definition_id=reversed_event.reward_definition_id,
            badge_definition_id=reversed_event.badge_definition_id,
            source_type=source_type,
            source_reference=source_reference,
            is_reversal=True,
            reversed_event_id=reversed_event.id,
            status=status,
            event_metadata=metadata,
            created_at=created_at,
        )
        self._db.add(reversal_event)
        self._db.flush()

        revoked_reward_grant_ids: list[UUID] = []
        for reward_grant in self._db.scalars(
            select(RewardGrant).where(
                RewardGrant.account_id == account_id,
                RewardGrant.source_reward_event_id == reversed_event.id,
                RewardGrant.revoked_at.is_(None),
            )
        ).all():
            reward_grant.status = "revoked"
            reward_grant.revoked_at = created_at
            reward_grant.revocation_reason = revocation_reason
            revoked_reward_grant_ids.append(reward_grant.id)

        revoked_badge_ids: list[UUID] = []
        for account_badge in self._db.scalars(
            select(AccountBadge).where(
                AccountBadge.account_id == account_id,
                AccountBadge.source_reward_event_id == reversed_event.id,
                AccountBadge.revoked_at.is_(None),
            )
        ).all():
            account_badge.revoked_at = created_at
            account_badge.revocation_reason = revocation_reason
            revoked_badge_ids.append(account_badge.id)

        reward_account = self._recompute_reward_account(account_id, recomputed_at=created_at)
        self._db.commit()

        return RewardEventApplicationRecord(
            event_id=reversal_event.id,
            account_id=account_id,
            event_type=reversal_event.event_type,
            points_delta=reversal_event.points_delta,
            is_reversal=reversal_event.is_reversal,
            reversed_event_id=reversal_event.reversed_event_id,
            status=reversal_event.status,
            source_type=reversal_event.source_type,
            source_reference=reversal_event.source_reference,
            created_at=reversal_event.created_at,
            metadata=reversal_event.event_metadata,
            reward_account=reward_account,
            revoked_reward_grant_ids=revoked_reward_grant_ids,
            revoked_badge_ids=revoked_badge_ids,
        )

    def complete_objective(
        self,
        *,
        account_id: UUID,
        objective_definition_id: UUID,
        increment_by: int,
        progress_at: datetime,
        metadata: dict[str, object],
    ) -> ObjectiveProgressUpdateRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        objective_definition = self._db.get(ObjectiveDefinition, objective_definition_id)
        if objective_definition is None:
            return None

        progress = self._db.scalar(
            select(AccountObjectiveProgress).where(
                AccountObjectiveProgress.account_id == account_id,
                AccountObjectiveProgress.objective_definition_id == objective_definition_id,
            )
        )
        if progress is None:
            progress = AccountObjectiveProgress(
                account_id=account_id,
                objective_definition_id=objective_definition_id,
                current_count=0,
                completed_count=0,
                repeat_iteration=1 if objective_definition.is_repeatable else None,
                status="not_started",
                progress_metadata={},
            )
            self._db.add(progress)
            self._db.flush()

        progress.progress_metadata = {**progress.progress_metadata, **metadata}
        progress.last_progress_at = progress_at
        completed_now = False

        if objective_definition.is_repeatable:
            cycle_total = progress.current_count + increment_by
            completions_gained, remainder = divmod(cycle_total, objective_definition.required_count)
            progress.current_count = remainder
            progress.status = (
                "in_progress"
                if (progress.current_count > 0 or completions_gained > 0)
                else "not_started"
            )
            if completions_gained > 0:
                progress.completed_count += completions_gained
                progress.last_completed_at = progress_at
                progress.repeat_iteration = (progress.repeat_iteration or 1) + completions_gained
                completed_now = True
        else:
            if progress.status != "completed":
                progress.current_count = min(
                    progress.current_count + increment_by,
                    objective_definition.required_count,
                )
                if progress.current_count >= objective_definition.required_count:
                    progress.completed_count = max(progress.completed_count, 1)
                    progress.last_completed_at = progress_at
                    progress.status = "completed"
                    completed_now = True
                elif progress.current_count > 0:
                    progress.status = "in_progress"
                else:
                    progress.status = "not_started"

        self._db.commit()

        return ObjectiveProgressUpdateRecord(
            account_id=account_id,
            objective_definition_id=objective_definition_id,
            objective_code=objective_definition.objective_code,
            required_count=objective_definition.required_count,
            current_count=progress.current_count,
            completed_count=progress.completed_count,
            repeat_iteration=progress.repeat_iteration,
            status=progress.status,
            last_completed_at=progress.last_completed_at,
            last_progress_at=progress.last_progress_at or progress_at,
            metadata=progress.progress_metadata,
            completed_now=completed_now,
        )

    def queue_notification(
        self,
        *,
        account_id: UUID,
        notification_type: str,
        queued_at: datetime,
        metadata: dict[str, object],
        status: str = "queued",
        objective_definition_id: UUID | None = None,
        reward_grant_id: UUID | None = None,
        badge_definition_id: UUID | None = None,
        reward_event_id: UUID | None = None,
    ) -> RewardNotificationQueueRecord | None:
        if self._db.get(Account, account_id) is None:
            return None

        current_max_sequence = self._db.scalar(
            select(func.max(RewardNotification.sequence_order)).where(
                RewardNotification.account_id == account_id
            )
        )
        sequence_order = (current_max_sequence or 0) + 1

        notification = RewardNotification(
            account_id=account_id,
            notification_type=notification_type,
            objective_definition_id=objective_definition_id,
            reward_grant_id=reward_grant_id,
            badge_definition_id=badge_definition_id,
            reward_event_id=reward_event_id,
            status=status,
            queued_at=queued_at,
            sequence_order=sequence_order,
            notification_metadata=metadata,
        )
        self._db.add(notification)
        self._db.commit()

        return RewardNotificationQueueRecord(
            notification_id=notification.id,
            account_id=account_id,
            notification_type=notification.notification_type,
            status=notification.status,
            sequence_order=notification.sequence_order,
            queued_at=notification.queued_at,
            metadata=notification.notification_metadata,
        )

    def _recompute_reward_account(
        self,
        account_id: UUID,
        *,
        recomputed_at: datetime,
    ) -> RewardAccountSnapshotRecord:
        reward_account = self._db.get(RewardAccount, account_id)
        if reward_account is None:
            reward_account = RewardAccount(account_id=account_id)
            self._db.add(reward_account)
            self._db.flush()

        total_points = int(
            self._db.scalar(
                select(func.coalesce(func.sum(RewardEvent.points_delta), 0)).where(
                    RewardEvent.account_id == account_id
                )
            )
            or 0
        )
        effective_points = max(total_points, 0)
        tier_code, tier_progress, next_milestone_points = _tier_summary_for_points(effective_points)

        reward_account.current_points = effective_points
        reward_account.current_tier = tier_code
        reward_account.current_tier_progress_points = tier_progress
        reward_account.next_milestone_points = next_milestone_points
        reward_account.last_recomputed_at = recomputed_at

        return RewardAccountSnapshotRecord(
            account_id=account_id,
            current_points=reward_account.current_points,
            current_tier=reward_account.current_tier,
            current_tier_progress_points=reward_account.current_tier_progress_points,
            next_milestone_points=reward_account.next_milestone_points,
            last_recomputed_at=recomputed_at,
        )


def _tier_summary_for_points(total_points: int) -> tuple[str, int, int]:
    if total_points < 1000:
        tier_code = "BRONZE"
    elif total_points < 2000:
        tier_code = "SILVER"
    elif total_points < 3000:
        tier_code = "GOLD"
    elif total_points < 4000:
        tier_code = "PLATINUM"
    else:
        tier_code = "PLUS"

    tier_progress = total_points % 1000
    next_milestone = ((total_points // 100) + 1) * 100
    return tier_code, tier_progress, min(next_milestone, _MAX_MILESTONE_POINTS)
