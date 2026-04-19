from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LauncherBlockingReason(BaseModel):
    code: str
    message: str


class LauncherPayProjectionSummary(BaseModel):
    source: Literal["pay_projection"] = "pay_projection"
    entitlement_status: str | None = None
    subscription_status: str | None = None
    product_access_state: str | None = None
    provisioning_state: str | None = None
    last_synced_at: datetime | None = None


class LauncherProductSummary(BaseModel):
    product_code: str
    product_name: str
    display_tag: str | None = None
    pay_projection: LauncherPayProjectionSummary | None = None
    access_state: str
    can_launch: bool
    launch_url: str | None = None
    blocked_reason: LauncherBlockingReason | None = None
    status_message: str | None = None


class LauncherProductsResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    products: list[LauncherProductSummary] = Field(default_factory=list)
