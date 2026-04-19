from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.addresses import AddressCreateRequest, AddressUpdateRequest
from app.services.address_service import (
    AddressNotFoundError,
    AddressService,
    AddressUpdateValidationError,
)


@dataclass
class StubAddressRecord:
    address_id: object
    account_id: object
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


class StubUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class StubAddressRepository:
    def __init__(
        self,
        *,
        records: list[StubAddressRecord] | None = None,
        created_record: StubAddressRecord | None = None,
        updated_record: StubAddressRecord | None = None,
        primary_record: StubAddressRecord | None = None,
        delete_result: bool = True,
    ) -> None:
        self._records = records or []
        self._created_record = created_record
        self._updated_record = updated_record
        self._primary_record = primary_record
        self._delete_result = delete_result
        self.created_calls: list[dict[str, object]] = []
        self.updated_calls: list[dict[str, object]] = []
        self.deleted_calls: list[dict[str, object]] = []
        self.primary_calls: list[dict[str, object]] = []
        self.listed_account_ids: list[object] = []
        self.unit_of_work = StubUnitOfWork()

    def list_addresses_for_account(self, account_id):  # noqa: ANN001
        self.listed_account_ids.append(account_id)
        return self._records

    def create_address(self, account_id, *, address_data: dict[str, object]):  # noqa: ANN001
        self.created_calls.append({"account_id": account_id, "address_data": address_data})
        if self._created_record is None:
            raise AssertionError("Expected created_record for create_address")
        return self._created_record

    def update_address(self, account_id, address_id, *, updates: dict[str, object]):  # noqa: ANN001
        self.updated_calls.append(
            {"account_id": account_id, "address_id": address_id, "updates": updates}
        )
        return self._updated_record

    def delete_address(self, account_id, address_id):  # noqa: ANN001
        self.deleted_calls.append({"account_id": account_id, "address_id": address_id})
        return self._delete_result

    def set_primary_address(self, account_id, address_id):  # noqa: ANN001
        self.primary_calls.append({"account_id": account_id, "address_id": address_id})
        return self._primary_record

    def commit(self) -> None:
        self.unit_of_work.commit()

    def rollback(self) -> None:
        self.unit_of_work.rollback()


def _build_record(
    *,
    account_id: object | None = None,
    address_id: object | None = None,
) -> StubAddressRecord:
    return StubAddressRecord(
        address_id=address_id or uuid4(),
        account_id=account_id or uuid4(),
        address_type="billing",
        label="Home",
        full_name="Address User",
        line1="100 Main Street",
        line2="Suite 200",
        city_or_locality="Chicago",
        state_or_region="IL",
        postal_code="60601",
        country_code="US",
        country_name="United States",
        formatted_address="100 Main Street, Suite 200, Chicago, IL 60601, US",
        is_primary=False,
        created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
    )


def test_address_service_lists_safe_address_summaries() -> None:
    account_id = uuid4()
    record = _build_record(account_id=account_id)
    repository = StubAddressRepository(records=[record])
    service = AddressService(repository)

    response = service.list_addresses(account_id)

    assert repository.listed_account_ids == [account_id]
    assert response.model_dump(mode="json") == {
        "addresses": [
            {
                "address_id": str(record.address_id),
                "address_type": "billing",
                "label": "Home",
                "full_name": "Address User",
                "line1": "100 Main Street",
                "line2": "Suite 200",
                "city_or_locality": "Chicago",
                "state_or_region": "IL",
                "postal_code": "60601",
                "country_code": "US",
                "country_name": "United States",
                "formatted_address": "100 Main Street, Suite 200, Chicago, IL 60601, US",
                "is_primary": False,
                "created_at": "2026-04-18T12:00:00Z",
                "updated_at": "2026-04-18T12:30:00Z",
            }
        ]
    }


def test_address_service_creates_address_and_commits() -> None:
    account_id = uuid4()
    created_record = _build_record(account_id=account_id)
    repository = StubAddressRepository(created_record=created_record)
    service = AddressService(repository)

    response = service.create_address(
        account_id,
        AddressCreateRequest(
            address_type="billing",
            label="Home",
            full_name="Address User",
            line1="100 Main Street",
            line2="Suite 200",
            city_or_locality="Chicago",
            state_or_region="IL",
            postal_code="60601",
            country_code="us",
            country_name="United States",
            formatted_address="100 Main Street, Suite 200, Chicago, IL 60601, US",
        ),
    )

    assert repository.created_calls == [
        {
            "account_id": account_id,
            "address_data": {
                "address_type": "billing",
                "label": "Home",
                "full_name": "Address User",
                "line1": "100 Main Street",
                "line2": "Suite 200",
                "city_or_locality": "Chicago",
                "state_or_region": "IL",
                "postal_code": "60601",
                "country_code": "US",
                "country_name": "United States",
                "formatted_address": "100 Main Street, Suite 200, Chicago, IL 60601, US",
            },
        }
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.address.country_code == "US"


def test_address_service_updates_existing_address_and_commits() -> None:
    account_id = uuid4()
    address_id = uuid4()
    updated_record = _build_record(account_id=account_id, address_id=address_id)
    repository = StubAddressRepository(updated_record=updated_record)
    service = AddressService(repository)

    response = service.update_address(
        account_id,
        address_id,
        AddressUpdateRequest(
            label="Office",
            city_or_locality="Austin",
            country_code="us",
        ),
    )

    assert repository.updated_calls == [
        {
            "account_id": account_id,
            "address_id": address_id,
            "updates": {
                "label": "Office",
                "city_or_locality": "Austin",
                "country_code": "US",
            },
        }
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.address.address_id == address_id


def test_address_service_rejects_empty_update_payload() -> None:
    service = AddressService(StubAddressRepository())

    try:
        service.update_address(uuid4(), uuid4(), AddressUpdateRequest())
    except AddressUpdateValidationError:
        pass
    else:
        raise AssertionError("Expected empty update payload to raise AddressUpdateValidationError")


def test_address_service_raises_not_found_for_missing_update_target() -> None:
    repository = StubAddressRepository(updated_record=None)
    service = AddressService(repository)

    try:
        service.update_address(uuid4(), uuid4(), AddressUpdateRequest(label="Updated"))
    except AddressNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing address update to raise AddressNotFoundError")

    assert repository.unit_of_work.commits == 0
    assert repository.unit_of_work.rollbacks == 1


def test_address_service_deletes_existing_address_and_commits() -> None:
    account_id = uuid4()
    address_id = uuid4()
    repository = StubAddressRepository(delete_result=True)
    service = AddressService(repository)

    response = service.delete_address(account_id, address_id)

    assert repository.deleted_calls == [
        {"account_id": account_id, "address_id": address_id}
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.model_dump() == {
        "success": True,
        "message": "Address deleted.",
    }


def test_address_service_raises_not_found_for_missing_delete_target() -> None:
    repository = StubAddressRepository(delete_result=False)
    service = AddressService(repository)

    try:
        service.delete_address(uuid4(), uuid4())
    except AddressNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing address delete to raise AddressNotFoundError")

    assert repository.unit_of_work.commits == 0
    assert repository.unit_of_work.rollbacks == 1


def test_address_service_sets_primary_address_and_commits() -> None:
    account_id = uuid4()
    address_id = uuid4()
    primary_record = _build_record(account_id=account_id, address_id=address_id)
    primary_record.is_primary = True
    repository = StubAddressRepository(primary_record=primary_record)
    service = AddressService(repository)

    response = service.set_primary_address(account_id, address_id)

    assert repository.primary_calls == [
        {"account_id": account_id, "address_id": address_id}
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.model_dump(mode="json")["address"]["is_primary"] is True


def test_address_service_raises_not_found_for_missing_primary_target() -> None:
    repository = StubAddressRepository(primary_record=None)
    service = AddressService(repository)

    try:
        service.set_primary_address(uuid4(), uuid4())
    except AddressNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing address set-primary to raise AddressNotFoundError")

    assert repository.unit_of_work.commits == 0
    assert repository.unit_of_work.rollbacks == 1
