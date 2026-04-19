from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RewardBadgeGalleryItem(BaseModel):
    badge_code: str
    display_name: str
    description: str
    icon_ref: str | None
    earned: bool
    earned_at: datetime | None


class RewardBadgeGalleryResponse(BaseModel):
    account_id: UUID
    badges: list[RewardBadgeGalleryItem]
