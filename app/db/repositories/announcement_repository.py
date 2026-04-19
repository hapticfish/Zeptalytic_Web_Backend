from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.announcements import Announcement


@dataclass(slots=True)
class AnnouncementRecord:
    announcement_id: UUID
    scope: str
    product_code: str | None
    title: str
    body: str
    severity: str
    published_at: datetime
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AnnouncementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_active_announcements(
        self,
        *,
        product_codes: list[str] | None = None,
        limit: int = 10,
        now: datetime | None = None,
    ) -> list[AnnouncementRecord]:
        effective_now = now or datetime.now(timezone.utc)
        statement = (
            select(Announcement)
            .where(Announcement.published_at <= effective_now)
            .where(
                or_(
                    Announcement.expires_at.is_(None),
                    Announcement.expires_at > effective_now,
                )
            )
            .order_by(Announcement.published_at.desc(), Announcement.id.desc())
            .limit(limit)
        )
        if product_codes:
            statement = statement.where(
                or_(
                    Announcement.scope == "global",
                    Announcement.product_code.is_(None),
                    Announcement.product_code.in_(product_codes),
                )
            )

        rows = self._db.scalars(statement).all()
        return [self._to_record(row) for row in rows]

    @staticmethod
    def _to_record(row: Announcement) -> AnnouncementRecord:
        return AnnouncementRecord(
            announcement_id=row.id,
            scope=row.scope,
            product_code=row.product_code,
            title=row.title,
            body=row.body,
            severity=row.severity,
            published_at=row.published_at,
            expires_at=row.expires_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
