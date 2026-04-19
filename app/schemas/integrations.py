from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DiscordIntegrationSummary(BaseModel):
    account_id: UUID
    username: str | None = None
    integration_status: Literal["connected", "disconnected", "error", "pending"]
    created_at: datetime
    updated_at: datetime


class DiscordIntegrationReadResponse(BaseModel):
    discord: DiscordIntegrationSummary


class DiscordConnectInitiationResponse(BaseModel):
    authorization_url: str
