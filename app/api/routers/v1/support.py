from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    get_audit_hook,
    get_rate_limiter,
    get_support_service,
    require_authenticated_session_context,
)
from app.core.config import settings
from app.schemas.support import (
    SupportTicketCreateRequest,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
)
from app.services import AuthenticatedSessionContext, SupportService
from app.utils.audit import AuditHook, emit_audit_event
from app.utils.rate_limits import (
    InMemoryRateLimiter,
    build_authenticated_rate_limit_key,
    build_support_ticket_rate_limit_policy,
)

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
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: SupportService = Depends(get_support_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> SupportTicketCreateResponse:
    rate_limiter.check(
        action="support_ticket_create",
        key=build_authenticated_rate_limit_key(request, account_id=context.account_id),
        policy=build_support_ticket_rate_limit_policy(settings),
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="support.ticket_create",
        outcome="attempt",
        account_id=context.account_id,
        metadata={
            "request_type": payload.request_type,
            "related_product_code": payload.related_product_code,
            "priority": payload.priority,
            "attachment_count": len(payload.attachments),
        },
    )
    response = service.create_ticket(context, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="support.ticket_create",
        outcome="success",
        account_id=context.account_id,
        metadata={
            "request_type": payload.request_type,
            "related_product_code": payload.related_product_code,
            "priority": payload.priority,
            "attachment_count": len(payload.attachments),
        },
    )
    return response
