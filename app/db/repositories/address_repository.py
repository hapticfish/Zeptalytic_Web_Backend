from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.addresses import Address


@dataclass(slots=True)
class AddressRecord:
    address_id: UUID
    account_id: UUID
    address_type: str
    label: str | None
    full_name: str
    line1: str
    line2: str | None
    city_or_locality: str
    state_or_region: str | None
    postal_code: str | None
    country_code: str
    country_name: str | None
    formatted_address: str | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class AddressRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def list_addresses_for_account(self, account_id: UUID) -> list[AddressRecord]:
        addresses = self._db.scalars(
            select(Address)
            .where(Address.account_id == account_id)
            .order_by(Address.is_primary.desc(), Address.created_at.asc(), Address.id.asc())
        ).all()
        return [self._to_record(address) for address in addresses]

    def create_address(
        self,
        account_id: UUID,
        *,
        address_data: dict[str, object],
    ) -> AddressRecord:
        address = Address(account_id=account_id, **address_data)
        self._db.add(address)
        self._db.flush()
        return self._to_record(address)

    def update_address(
        self,
        account_id: UUID,
        address_id: UUID,
        *,
        updates: dict[str, object],
    ) -> AddressRecord | None:
        address = self._db.scalar(
            select(Address).where(Address.id == address_id, Address.account_id == account_id)
        )
        if address is None:
            return None

        for field_name, value in updates.items():
            setattr(address, field_name, value)

        self._db.flush()
        return self._to_record(address)

    def delete_address(self, account_id: UUID, address_id: UUID) -> bool:
        address = self._db.scalar(
            select(Address).where(Address.id == address_id, Address.account_id == account_id)
        )
        if address is None:
            return False

        self._db.delete(address)
        self._db.flush()
        return True

    def set_primary_address(
        self,
        account_id: UUID,
        address_id: UUID,
    ) -> AddressRecord | None:
        address = self._db.scalar(
            select(Address).where(Address.id == address_id, Address.account_id == account_id)
        )
        if address is None:
            return None

        self._db.execute(
            update(Address)
            .where(Address.account_id == account_id, Address.id != address_id)
            .values(is_primary=False)
        )
        address.is_primary = True
        self._db.flush()
        return self._to_record(address)

    @staticmethod
    def _to_record(address: Address) -> AddressRecord:
        return AddressRecord(
            address_id=address.id,
            account_id=address.account_id,
            address_type=address.address_type,
            label=address.label,
            full_name=address.full_name,
            line1=address.line1,
            line2=address.line2,
            city_or_locality=address.city_or_locality,
            state_or_region=address.state_or_region,
            postal_code=address.postal_code,
            country_code=address.country_code,
            country_name=address.country_name,
            formatted_address=address.formatted_address,
            is_primary=address.is_primary,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )
