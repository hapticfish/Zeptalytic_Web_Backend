from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import MutationSuccessResponse


class CommunicationPreferenceSummary(BaseModel):
    account_id: UUID
    marketing_emails_enabled: bool
    product_updates_enabled: bool
    announcement_emails_enabled: bool
    created_at: datetime
    updated_at: datetime


class CommunicationPreferenceReadResponse(BaseModel):
    preferences: CommunicationPreferenceSummary


class CommunicationPreferenceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    marketing_emails_enabled: bool | None = None
    product_updates_enabled: bool | None = None
    announcement_emails_enabled: bool | None = None


class CommunicationPreferenceRouteContractResponse(MutationSuccessResponse):
    message: str = "Communication preferences router registered."
    scope: Literal["communication_preferences"] = "communication_preferences"
    guard: Literal["normal_authenticated_verified"] = "normal_authenticated_verified"
