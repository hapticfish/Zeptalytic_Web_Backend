from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.address_repository import AddressRepository
from app.schemas.addresses import (
    AddressCreateRequest,
    AddressDeleteResponse,
    AddressListResponse,
    AddressReadResponse,
    AddressRouteContractResponse,
    AddressSummary,
    AddressUpdateRequest,
)


class AddressNotFoundError(Exception):
    """Raised when an address does not exist for the requested account."""


class AddressUpdateValidationError(Exception):
    """Raised when an address mutation payload is invalid."""


class AddressService:
    def __init__(self, repository: AddressRepository) -> None:
        self._repository = repository

    def describe_contract(self) -> AddressRouteContractResponse:
        return AddressRouteContractResponse()

    def list_addresses(self, account_id) -> AddressListResponse:  # noqa: ANN001
        records = self._repository.list_addresses_for_account(account_id)
        return AddressListResponse(
            addresses=[self._build_summary(record) for record in records]
        )

    def create_address(
        self,
        account_id,
        payload: AddressCreateRequest,  # noqa: ANN001
    ) -> AddressReadResponse:
        record = self._repository.create_address(
            account_id,
            address_data=payload.model_dump(),
        )
        self._repository.commit()
        return AddressReadResponse(address=self._build_summary(record))

    def update_address(
        self,
        account_id,
        address_id,
        payload: AddressUpdateRequest,  # noqa: ANN001
    ) -> AddressReadResponse:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AddressUpdateValidationError(
                "At least one address field must be provided."
            )

        record = self._repository.update_address(account_id, address_id, updates=updates)
        if record is None:
            self._repository.rollback()
            raise AddressNotFoundError(f"Address {address_id} was not found.")

        self._repository.commit()
        return AddressReadResponse(address=self._build_summary(record))

    def delete_address(self, account_id, address_id) -> AddressDeleteResponse:  # noqa: ANN001
        deleted = self._repository.delete_address(account_id, address_id)
        if not deleted:
            self._repository.rollback()
            raise AddressNotFoundError(f"Address {address_id} was not found.")

        self._repository.commit()
        return AddressDeleteResponse()

    def set_primary_address(self, account_id, address_id) -> AddressReadResponse:  # noqa: ANN001
        record = self._repository.set_primary_address(account_id, address_id)
        if record is None:
            self._repository.rollback()
            raise AddressNotFoundError(f"Address {address_id} was not found.")

        self._repository.commit()
        return AddressReadResponse(address=self._build_summary(record))

    @staticmethod
    def _build_summary(record) -> AddressSummary:  # noqa: ANN001
        return AddressSummary(
            address_id=record.address_id,
            address_type=record.address_type,
            label=record.label,
            full_name=record.full_name,
            line1=record.line1,
            line2=record.line2,
            city_or_locality=record.city_or_locality,
            state_or_region=record.state_or_region,
            postal_code=record.postal_code,
            country_code=record.country_code,
            country_name=record.country_name,
            formatted_address=record.formatted_address,
            is_primary=record.is_primary,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def build_address_service(db: Session) -> AddressService:
    return AddressService(AddressRepository(db))
