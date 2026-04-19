from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_profile_settings_service,
    require_normal_authenticated_session_context,
)
from app.schemas.profiles import ProfileRouteContractResponse, ProfileSettingsReadResponse
from app.services import AuthenticatedSessionContext, ProfileSettingsService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/_contract", response_model=ProfileRouteContractResponse, include_in_schema=False)
def get_profiles_contract(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: ProfileSettingsService = Depends(get_profile_settings_service),
) -> ProfileRouteContractResponse:
    del context
    return service.describe_contract()


@router.get("/me", response_model=ProfileSettingsReadResponse)
def get_my_profile_settings(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: ProfileSettingsService = Depends(get_profile_settings_service),
) -> ProfileSettingsReadResponse:
    return service.get_profile_settings(context.account_id)
