from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_announcement_service, require_authenticated_session_context
from app.schemas.announcements import AnnouncementListResponse
from app.services import AnnouncementService, AuthenticatedSessionContext

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=AnnouncementListResponse)
def list_announcements(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: AnnouncementService = Depends(get_announcement_service),
    limit: int = Query(default=10, ge=1, le=100),
    cursor: str | None = Query(default=None),
    product_code: list[str] | None = Query(default=None),
) -> AnnouncementListResponse:
    del context
    return service.list_announcements(
        product_codes=product_code,
        limit=limit,
        cursor=cursor,
    )
