from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models.rewards.account_badges import AccountBadge
from app.db.models.rewards.badge_definitions import BadgeDefinition


@dataclass(slots=True)
class RewardBadgeGalleryRecord:
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None
    earned_at: datetime | None


class RewardBadgeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_badges_for_account(self, account_id: UUID) -> list[RewardBadgeGalleryRecord]:
        rows = self._db.execute(
            select(BadgeDefinition, AccountBadge)
            .outerjoin(
                AccountBadge,
                and_(
                    AccountBadge.badge_definition_id == BadgeDefinition.id,
                    AccountBadge.account_id == account_id,
                    AccountBadge.revoked_at.is_(None),
                ),
            )
            .order_by(
                AccountBadge.earned_at.desc().nullslast(),
                BadgeDefinition.display_name.asc(),
            )
        ).all()

        return [
            RewardBadgeGalleryRecord(
                badge_code=badge_definition.badge_code,
                display_name=badge_definition.display_name,
                description=badge_definition.description,
                icon_ref=badge_definition.icon_ref,
                earned_at=account_badge.earned_at if account_badge is not None else None,
            )
            for badge_definition, account_badge in rows
        ]
