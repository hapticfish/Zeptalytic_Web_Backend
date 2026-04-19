from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.address_repository import AddressRepository
from app.schemas.addresses import AddressRouteContractResponse


class AddressService:
    def __init__(self, repository: AddressRepository) -> None:
        self._repository = repository

    def describe_contract(self) -> AddressRouteContractResponse:
        return AddressRouteContractResponse()


def build_address_service(db: Session) -> AddressService:
    return AddressService(AddressRepository(db))
