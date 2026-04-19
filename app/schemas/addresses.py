from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class AddressListResponse(BaseModel):
    addresses: list[AddressSummary]


class AddressReadResponse(BaseModel):
    address: AddressSummary


class AddressDeleteResponse(MutationSuccessResponse):
    message: str = "Address deleted."


class AddressCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    address_type: Literal["billing", "shipping"]
    label: str | None = Field(default=None, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city_or_locality: str = Field(min_length=1, max_length=128)
    state_or_region: str | None = Field(default=None, max_length=128)
    postal_code: str | None = Field(default=None, max_length=32)
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str | None = Field(default=None, max_length=128)
    formatted_address: str | None = Field(default=None, max_length=1024)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class AddressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    address_type: Literal["billing", "shipping"] | None = None
    label: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    line1: str | None = Field(default=None, min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city_or_locality: str | None = Field(default=None, min_length=1, max_length=128)
    state_or_region: str | None = Field(default=None, max_length=128)
    postal_code: str | None = Field(default=None, max_length=32)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    country_name: str | None = Field(default=None, max_length=128)
    formatted_address: str | None = Field(default=None, max_length=1024)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()


class AddressRouteContractResponse(MutationSuccessResponse):
    message: str = "Addresses router registered."
    scope: Literal["addresses"] = "addresses"
    guard: Literal["normal_authenticated_verified"] = "normal_authenticated_verified"
