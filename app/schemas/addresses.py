from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import MutationSuccessResponse


class AddressSummary(BaseModel):
    address_id: UUID
    address_type: Literal["billing", "shipping"]
    label: str | None = None
    full_name: str
    line1: str
    line2: str | None = None
    city_or_locality: str
    state_or_region: str | None = None
    postal_code: str | None = None
    country_code: str
    country_name: str | None = None
    formatted_address: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class AddressRouteContractResponse(MutationSuccessResponse):
    message: str = "Addresses router registered."
    scope: Literal["addresses"] = "addresses"
    guard: Literal["normal_authenticated_verified"] = "normal_authenticated_verified"
