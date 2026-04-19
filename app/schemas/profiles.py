from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import MutationSuccessResponse


class DiscordProfileDisplaySummary(BaseModel):
    username: str | None = None
    integration_status: Literal["connected", "disconnected", "error", "pending"]


class ProfileSettingsSummary(BaseModel):
    account_id: UUID
    username: str
    email: str
    display_name: str | None = None
    phone: str | None = None
    timezone: str | None = None
    profile_image_url: str | None = None
    preferred_language: str | None = None
    discord: DiscordProfileDisplaySummary
    created_at: datetime
    updated_at: datetime


class ProfileSettingsReadResponse(BaseModel):
    profile: ProfileSettingsSummary


class ProfileSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    phone: str | None = None
    timezone: str | None = None
    profile_image_url: str | None = None
    preferred_language: str | None = None


class ProfileRouteContractResponse(MutationSuccessResponse):
    message: str = "Profiles router registered."
    scope: Literal["profiles"] = "profiles"
    guard: Literal["normal_authenticated_verified"] = "normal_authenticated_verified"
