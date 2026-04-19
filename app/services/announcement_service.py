from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories.announcement_repository import AnnouncementRepository
from app.schemas.announcements import AnnouncementListItem, AnnouncementListResponse
from app.schemas.common import CursorPageInfo

DEFAULT_ANNOUNCEMENT_LIMIT = 10
MAX_ANNOUNCEMENT_LIMIT = 100


class AnnouncementService:
    def __init__(self, repository: AnnouncementRepository) -> None:
        self._repository = repository

    def list_announcements(
        self,
        *,
        product_codes: list[str] | None = None,
        limit: int = DEFAULT_ANNOUNCEMENT_LIMIT,
        cursor: str | None = None,
        now: datetime | None = None,
    ) -> AnnouncementListResponse:
        normalized_limit = max(1, min(limit, MAX_ANNOUNCEMENT_LIMIT))
        records = self._repository.list_active_announcements(
            product_codes=product_codes,
            limit=normalized_limit,
            now=now,
        )
        return AnnouncementListResponse(
            items=[
                AnnouncementListItem(
                    announcement_id=record.announcement_id,
                    scope=record.scope,
                    product_code=record.product_code,
                    title=record.title,
                    body=record.body,
                    severity=record.severity,
                    published_at=record.published_at,
                    expires_at=record.expires_at,
                )
                for record in records
            ],
            page=CursorPageInfo(limit=normalized_limit, cursor=cursor, next_cursor=None),
        )


def build_announcement_service(db: Session) -> AnnouncementService:
    return AnnouncementService(AnnouncementRepository(db))
