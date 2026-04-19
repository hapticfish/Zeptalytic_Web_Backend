from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_support_service, require_authenticated_session_context
from app.schemas.support import (
    SupportTicketCreateRequest,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
)
from app.services import AuthenticatedSessionContext, SupportService

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/tickets", response_model=SupportTicketListResponse)
def list_support_tickets(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: SupportService = Depends(get_support_service),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> SupportTicketListResponse:
    return service.list_tickets(context, limit=limit, cursor=cursor)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
def get_support_ticket_detail(
    ticket_id: UUID,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: SupportService = Depends(get_support_service),
) -> SupportTicketDetailResponse:
    return service.get_ticket_detail(context, ticket_id)


@router.post("/tickets", response_model=SupportTicketCreateResponse)
def create_support_ticket(
    payload: SupportTicketCreateRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: SupportService = Depends(get_support_service),
) -> SupportTicketCreateResponse:
    return service.create_ticket(context, payload)
