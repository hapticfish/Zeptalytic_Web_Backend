from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.billing import BillingSnapshotResponse
from app.schemas.launcher import LauncherProductsResponse


class DashboardProgressSummary(BaseModel):
    source: Literal["parent_owned"] = "parent_owned"
    current_points: int
    current_tier: str
    current_milestone: str | None = None
    next_milestone: str | None = None
    points_to_next_milestone: int | None = None
    subscription_level_hint: str | None = None


class DashboardSystemStatusSummary(BaseModel):
    source: Literal["parent_owned"] = "parent_owned"
    product_code: str
    product_name: str
    status: str
    headline: str | None = None
    detail: str | None = None
    updated_at: datetime | None = None


class DashboardNotificationSummary(BaseModel):
    source: Literal["parent_owned"] = "parent_owned"
    notification_type: str
    title: str
    body: str | None = None
    published_at: datetime
    cta_label: str | None = None
    cta_url: str | None = None


class DashboardSummaryResponse(BaseModel):
    launcher: LauncherProductsResponse
    billing: BillingSnapshotResponse
    parent_rewards_progress: DashboardProgressSummary | None = None
    parent_system_statuses: list[DashboardSystemStatusSummary] = Field(default_factory=list)
    parent_notifications: list[DashboardNotificationSummary] = Field(default_factory=list)
