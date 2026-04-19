from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_address_service,
    require_normal_authenticated_session_context,
)
from app.schemas.addresses import AddressRouteContractResponse
from app.services import AddressService, AuthenticatedSessionContext

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/_contract", response_model=AddressRouteContractResponse, include_in_schema=False)
def get_addresses_contract(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressRouteContractResponse:
    del context
    return service.describe_contract()
