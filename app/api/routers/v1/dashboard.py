from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_dashboard_service,
    require_normal_authenticated_session_context,
)
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import AuthenticatedSessionContext, DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    return service.get_summary(context)
