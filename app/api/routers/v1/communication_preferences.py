from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_communication_preference_service,
    require_normal_authenticated_session_context,
)
from app.schemas.communication_preferences import (
    CommunicationPreferenceReadResponse,
    CommunicationPreferenceRouteContractResponse,
    CommunicationPreferenceUpdateRequest,
)
from app.services import AuthenticatedSessionContext, CommunicationPreferenceService

router = APIRouter(prefix="/communication-preferences", tags=["communication-preferences"])


@router.get(
    "/_contract",
    response_model=CommunicationPreferenceRouteContractResponse,
    include_in_schema=False,
)
def get_communication_preferences_contract(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: CommunicationPreferenceService = Depends(get_communication_preference_service),
) -> CommunicationPreferenceRouteContractResponse:
    del context
    return service.describe_contract()


@router.get("/me", response_model=CommunicationPreferenceReadResponse)
def get_my_communication_preferences(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: CommunicationPreferenceService = Depends(get_communication_preference_service),
) -> CommunicationPreferenceReadResponse:
    return service.get_preferences(context.account_id)


@router.patch("/me", response_model=CommunicationPreferenceReadResponse)
def update_my_communication_preferences(
    payload: CommunicationPreferenceUpdateRequest,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: CommunicationPreferenceService = Depends(get_communication_preference_service),
) -> CommunicationPreferenceReadResponse:
    return service.update_preferences(context.account_id, payload)
