from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

ItemT = TypeVar("ItemT")


class MutationSuccessResponse(BaseModel):
    success: bool = True
    message: str


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorDetail


class CursorPageInfo(BaseModel):
    limit: int = Field(ge=1)
    cursor: str | None = None
    next_cursor: str | None = None


class CursorPageResponse(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    page: CursorPageInfo
