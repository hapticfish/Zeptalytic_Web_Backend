from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.db.vocabularies import SERVICE_STATUS

ServiceStatusValue = Literal["online", "degraded", "maintenance", "offline"]

ALLOWED_SERVICE_STATUS_VALUES = SERVICE_STATUS.allowed_values


class ServiceStatusListItem(BaseModel):
    status_id: UUID
    product_code: str
    status: ServiceStatusValue
    message: str | None = None
    updated_at: datetime


class ServiceStatusListResponse(BaseModel):
    items: list[ServiceStatusListItem]
