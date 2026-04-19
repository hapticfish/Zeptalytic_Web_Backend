from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.vocabularies import (
    ATTACHMENT_SCAN_STATUS,
    SUPPORT_PRIORITY,
    SUPPORT_REQUEST_TYPE,
    SUPPORT_TICKET_STATUS,
)
from app.schemas.common import CursorPageResponse, MutationSuccessResponse

SupportRequestType = Literal["billing", "sales", "feature_request", "technical_support"]
SupportPriority = Literal["low", "medium", "high", "urgent"]
SupportTicketStatus = Literal["open", "in_progress", "waiting_on_customer", "resolved", "closed"]
AttachmentScanStatus = Literal["pending", "clean", "infected", "failed"]

ALLOWED_SUPPORT_REQUEST_TYPES = SUPPORT_REQUEST_TYPE.allowed_values
ALLOWED_SUPPORT_PRIORITIES = SUPPORT_PRIORITY.allowed_values
ALLOWED_SUPPORT_TICKET_STATUSES = SUPPORT_TICKET_STATUS.allowed_values
ALLOWED_ATTACHMENT_SCAN_STATUSES = ATTACHMENT_SCAN_STATUS.allowed_values


class SupportAttachmentMetadataReference(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_reference: str = Field(min_length=1, max_length=128)
    original_filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    file_size_bytes: int = Field(ge=1, le=10 * 1024 * 1024)
    upload_token: str = Field(min_length=1, max_length=512)


class SupportAttachmentSummary(BaseModel):
    attachment_id: UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    scan_status: AttachmentScanStatus
    uploaded_at: datetime


class SupportTicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_type: SupportRequestType
    related_product_code: str | None = Field(default=None, min_length=1, max_length=64)
    priority: SupportPriority
    subject: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    attachments: list[SupportAttachmentMetadataReference] = Field(default_factory=list, max_length=5)


class SupportTicketSummary(BaseModel):
    ticket_id: UUID
    ticket_code: str
    request_type: SupportRequestType
    related_product_code: str | None = None
    priority: SupportPriority
    subject: str
    status: SupportTicketStatus
    estimated_response_sla_label: str | None = None
    created_at: datetime
    updated_at: datetime
    attachment_count: int = Field(ge=0)


class SupportTicketDetailResponse(BaseModel):
    ticket: SupportTicketSummary
    description: str
    attachments: list[SupportAttachmentSummary] = Field(default_factory=list)


class SupportTicketListResponse(CursorPageResponse[SupportTicketSummary]):
    pass


class SupportTicketCreateResponse(MutationSuccessResponse):
    ticket: SupportTicketSummary


class SupportRouteContractResponse(MutationSuccessResponse):
    action: Literal["create_ticket", "list_tickets", "read_ticket"]
