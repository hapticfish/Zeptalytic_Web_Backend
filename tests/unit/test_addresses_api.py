from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_address_service, get_auth_service
from app.main import app
from app.schemas.addresses import (
    AddressListResponse,
    AddressReadResponse,
    AddressSummary,
)
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)
from tests.unit.assertions import assert_standard_error_response


class StubAddressService:
    def __init__(
        self,
        *,
        list_response: AddressListResponse | None = None,
        read_response: AddressReadResponse | None = None,
    ) -> None:
        self._list_response = list_response or AddressListResponse(addresses=[])
        self._read_response = read_response
        self.created_calls: list[dict[str, object]] = []
        self.updated_calls: list[dict[str, object]] = []
        self.deleted_calls: list[dict[str, object]] = []
        self.primary_calls: list[dict[str, object]] = []

    def describe_contract(self):  # noqa: ANN001
        return {
            "success": True,
            "message": "Addresses router registered.",
            "scope": "addresses",
            "guard": "normal_authenticated_verified",
        }

    def list_addresses(self, account_id):  # noqa: ANN001
        return self._list_response

    def create_address(self, account_id, payload):  # noqa: ANN001
        if self._read_response is None:
            from app.services.address_service import AddressNotFoundError

            raise AddressNotFoundError(f"missing {account_id}")
        self.created_calls.append(
            {
                "account_id": account_id,
                "payload": payload.model_dump(exclude_unset=True),
            }
        )
        return self._read_response

    def update_address(self, account_id, address_id, payload):  # noqa: ANN001
        if self._read_response is None:
            from app.services.address_service import AddressNotFoundError

            raise AddressNotFoundError(f"missing {address_id}")
        self.updated_calls.append(
            {
                "account_id": account_id,
                "address_id": address_id,
                "payload": payload.model_dump(exclude_unset=True),
            }
        )
        return self._read_response

    def delete_address(self, account_id, address_id):  # noqa: ANN001
        if self._read_response is None:
            from app.services.address_service import AddressNotFoundError

            raise AddressNotFoundError(f"missing {address_id}")
        self.deleted_calls.append(
            {
                "account_id": account_id,
                "address_id": address_id,
            }
        )
        return {"success": True, "message": "Address deleted."}

    def set_primary_address(self, account_id, address_id):  # noqa: ANN001
        if self._read_response is None:
            from app.services.address_service import AddressNotFoundError

            raise AddressNotFoundError(f"missing {address_id}")
        self.primary_calls.append(
            {
                "account_id": account_id,
                "address_id": address_id,
            }
        )
        return self._read_response


class StubAuthService:
    def __init__(self, context: AuthenticatedSessionContext | None) -> None:
        self._context = context
        self.received_tokens: list[str | None] = []

    def get_authenticated_session_context(
        self,
        session_token: str | None,
    ) -> AuthenticatedSessionContext | None:
        self.received_tokens.append(session_token)
        return self._context

    @staticmethod
    def ensure_account_status_allows_authenticated_access(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context

    @staticmethod
    def ensure_email_verified(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        if context.status == "pending_verification" or context.email_verified_at is None:
            raise EmailVerificationRequiredError("Email verification is required.")
        return context

    @staticmethod
    def ensure_account_status_allows_normal_authenticated_actions(
        context: AuthenticatedSessionContext,
    ) -> AuthenticatedSessionContext:
        return context


def _build_context(
    *,
    status: str = "active",
    email_verified_at: datetime | None = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
) -> AuthenticatedSessionContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="address-user",
        email="address-user@example.com",
        status=status,
        role="user",
        email_verified_at=email_verified_at,
        session_created_at=now - timedelta(hours=1),
        session_expires_at=now + timedelta(hours=1),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest-client",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


client = TestClient(app)


def test_addresses_contract_endpoint_uses_verified_session_guard() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: StubAddressService()

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.get("/api/v1/addresses/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["addresses-token"]
    assert response.json() == {
        "success": True,
        "message": "Addresses router registered.",
        "scope": "addresses",
        "guard": "normal_authenticated_verified",
    }


def test_addresses_contract_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: StubAddressService()

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.get("/api/v1/addresses/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=403,
        code="email_verification_required",
        message="Email verification is required.",
        details={},
    )


def test_addresses_me_endpoint_returns_address_list() -> None:
    context = _build_context()
    response_payload = AddressListResponse(
        addresses=[
            AddressSummary(
                address_id=uuid4(),
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
        ]
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = (
        lambda: StubAddressService(list_response=response_payload)
    )

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.get("/api/v1/addresses/me")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["addresses-token"]
    assert response.json() == {
        "addresses": [
            {
                "address_id": str(response_payload.addresses[0].address_id),
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


def test_addresses_post_me_endpoint_creates_address() -> None:
    context = _build_context()
    response_payload = AddressReadResponse(
        address=AddressSummary(
            address_id=uuid4(),
            address_type="billing",
            label="Home",
            full_name="Address User",
            line1="100 Main Street",
            line2=None,
            city_or_locality="Chicago",
            state_or_region="IL",
            postal_code="60601",
            country_code="US",
            country_name="United States",
            formatted_address="100 Main Street, Chicago, IL 60601, US",
            is_primary=False,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    address_service = StubAddressService(read_response=response_payload)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: address_service

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.post(
            "/api/v1/addresses/me",
            json={
                "address_type": "billing",
                "label": "Home",
                "full_name": "Address User",
                "line1": "100 Main Street",
                "city_or_locality": "Chicago",
                "state_or_region": "IL",
                "postal_code": "60601",
                "country_code": "us",
                "country_name": "United States",
                "formatted_address": "100 Main Street, Chicago, IL 60601, US",
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert address_service.created_calls == [
        {
            "account_id": context.account_id,
            "payload": {
                "address_type": "billing",
                "label": "Home",
                "full_name": "Address User",
                "line1": "100 Main Street",
                "city_or_locality": "Chicago",
                "state_or_region": "IL",
                "postal_code": "60601",
                "country_code": "US",
                "country_name": "United States",
                "formatted_address": "100 Main Street, Chicago, IL 60601, US",
            },
        }
    ]
    assert response.json()["address"]["country_code"] == "US"


def test_addresses_patch_me_endpoint_updates_existing_address() -> None:
    context = _build_context()
    address_id = uuid4()
    response_payload = AddressReadResponse(
        address=AddressSummary(
            address_id=address_id,
            address_type="shipping",
            label="Office",
            full_name="Address User",
            line1="200 Main Street",
            line2=None,
            city_or_locality="Austin",
            state_or_region="TX",
            postal_code="78701",
            country_code="US",
            country_name="United States",
            formatted_address="200 Main Street, Austin, TX 78701, US",
            is_primary=False,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    address_service = StubAddressService(read_response=response_payload)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: address_service

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.patch(
            f"/api/v1/addresses/me/{address_id}",
            json={
                "address_type": "shipping",
                "label": "Office",
                "city_or_locality": "Austin",
                "country_code": "us",
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert address_service.updated_calls == [
        {
            "account_id": context.account_id,
            "address_id": address_id,
            "payload": {
                "address_type": "shipping",
                "label": "Office",
                "city_or_locality": "Austin",
                "country_code": "US",
            },
        }
    ]
    assert response.json()["address"]["city_or_locality"] == "Austin"


def test_addresses_delete_me_endpoint_deletes_existing_address() -> None:
    context = _build_context()
    address_id = uuid4()
    auth_service = StubAuthService(context)
    address_service = StubAddressService(
        read_response=AddressReadResponse(
            address=AddressSummary(
                address_id=address_id,
                address_type="billing",
                label="Home",
                full_name="Address User",
                line1="100 Main Street",
                line2=None,
                city_or_locality="Chicago",
                state_or_region="IL",
                postal_code="60601",
                country_code="US",
                country_name="United States",
                formatted_address="100 Main Street, Chicago, IL 60601, US",
                is_primary=False,
                created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
            )
        )
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: address_service

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.delete(f"/api/v1/addresses/me/{address_id}")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert address_service.deleted_calls == [
        {
            "account_id": context.account_id,
            "address_id": address_id,
        }
    ]
    assert response.json() == {
        "success": True,
        "message": "Address deleted.",
    }


def test_addresses_post_primary_endpoint_sets_existing_primary_address() -> None:
    context = _build_context()
    address_id = uuid4()
    response_payload = AddressReadResponse(
        address=AddressSummary(
            address_id=address_id,
            address_type="billing",
            label="Home",
            full_name="Address User",
            line1="100 Main Street",
            line2=None,
            city_or_locality="Chicago",
            state_or_region="IL",
            postal_code="60601",
            country_code="US",
            country_name="United States",
            formatted_address="100 Main Street, Chicago, IL 60601, US",
            is_primary=True,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 45, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    address_service = StubAddressService(read_response=response_payload)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: address_service

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.post(f"/api/v1/addresses/me/{address_id}/primary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert address_service.primary_calls == [
        {
            "account_id": context.account_id,
            "address_id": address_id,
        }
    ]
    assert response.json()["address"]["is_primary"] is True


def test_addresses_patch_me_endpoint_returns_not_found_for_missing_address() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: StubAddressService(read_response=None)

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.patch(
            f"/api/v1/addresses/me/{uuid4()}",
            json={"label": "Updated"},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=404,
        code="address_not_found",
        message="Address not found.",
        details={},
    )


def test_addresses_post_primary_endpoint_returns_not_found_for_missing_address() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: StubAddressService(read_response=None)

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.post(f"/api/v1/addresses/me/{uuid4()}/primary")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert_standard_error_response(
        response,
        status_code=404,
        code="address_not_found",
        message="Address not found.",
        details={},
    )


def test_addresses_post_me_endpoint_rejects_invalid_address_type() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_address_service] = lambda: StubAddressService(
        read_response=AddressReadResponse(
            address=AddressSummary(
                address_id=uuid4(),
                address_type="billing",
                label=None,
                full_name="Address User",
                line1="100 Main Street",
                line2=None,
                city_or_locality="Chicago",
                state_or_region="IL",
                postal_code="60601",
                country_code="US",
                country_name="United States",
                formatted_address="100 Main Street, Chicago, IL 60601, US",
                is_primary=False,
                created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
            )
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "addresses-token")
        response = client.post(
            "/api/v1/addresses/me",
            json={
                "address_type": "office",
                "full_name": "Address User",
                "line1": "100 Main Street",
                "city_or_locality": "Chicago",
                "country_code": "US",
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
