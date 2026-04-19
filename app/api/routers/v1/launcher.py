from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_launcher_service,
    require_normal_authenticated_session_context,
)
from app.schemas.launcher import LauncherProductsResponse
from app.services import AuthenticatedSessionContext, LauncherService

router = APIRouter(prefix="/launcher", tags=["launcher"])


@router.get("/products", response_model=LauncherProductsResponse)
def list_launcher_products(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: LauncherService = Depends(get_launcher_service),
) -> LauncherProductsResponse:
    return service.get_products(context)
