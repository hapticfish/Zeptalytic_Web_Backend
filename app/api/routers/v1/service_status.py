from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_service_status_service, require_authenticated_session_context
from app.schemas.service_status import ServiceStatusListResponse
from app.services import AuthenticatedSessionContext, ServiceStatusService

router = APIRouter(prefix="/service-status", tags=["service-status"])


@router.get("", response_model=ServiceStatusListResponse)
def list_service_statuses(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: ServiceStatusService = Depends(get_service_status_service),
    product_code: list[str] | None = Query(default=None),
) -> ServiceStatusListResponse:
    del context
    return service.list_current_statuses(product_codes=product_code)
