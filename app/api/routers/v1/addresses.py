from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_address_service,
    require_normal_authenticated_session_context,
)
from app.schemas.addresses import (
    AddressCreateRequest,
    AddressDeleteResponse,
    AddressListResponse,
    AddressReadResponse,
    AddressRouteContractResponse,
    AddressUpdateRequest,
)
from app.services import AddressService, AuthenticatedSessionContext

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/_contract", response_model=AddressRouteContractResponse, include_in_schema=False)
def get_addresses_contract(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressRouteContractResponse:
    del context
    return service.describe_contract()


@router.get("/me", response_model=AddressListResponse)
def list_my_addresses(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressListResponse:
    return service.list_addresses(context.account_id)


@router.post("/me", response_model=AddressReadResponse)
def create_my_address(
    payload: AddressCreateRequest,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressReadResponse:
    return service.create_address(context.account_id, payload)


@router.patch("/me/{address_id}", response_model=AddressReadResponse)
def update_my_address(
    address_id: UUID,
    payload: AddressUpdateRequest,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressReadResponse:
    return service.update_address(context.account_id, address_id, payload)


@router.delete("/me/{address_id}", response_model=AddressDeleteResponse)
def delete_my_address(
    address_id: UUID,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressDeleteResponse:
    return service.delete_address(context.account_id, address_id)


@router.post("/me/{address_id}/primary", response_model=AddressReadResponse)
def set_my_primary_address(
    address_id: UUID,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: AddressService = Depends(get_address_service),
) -> AddressReadResponse:
    return service.set_primary_address(context.account_id, address_id)
