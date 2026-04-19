from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.db.vocabularies import ANNOUNCEMENT_SCOPE, ANNOUNCEMENT_SEVERITY
from app.schemas.common import CursorPageResponse

AnnouncementScope = Literal["global", "product"]
AnnouncementSeverity = Literal["info", "success", "warning", "critical"]

ALLOWED_ANNOUNCEMENT_SCOPES = ANNOUNCEMENT_SCOPE.allowed_values
ALLOWED_ANNOUNCEMENT_SEVERITIES = ANNOUNCEMENT_SEVERITY.allowed_values


class AnnouncementListItem(BaseModel):
    announcement_id: UUID
    scope: AnnouncementScope
    product_code: str | None = None
    title: str
    body: str
    severity: AnnouncementSeverity
    published_at: datetime
    expires_at: datetime | None = None


class AnnouncementListResponse(CursorPageResponse[AnnouncementListItem]):
    pass
