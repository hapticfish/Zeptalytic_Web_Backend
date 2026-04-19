from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_communication_preference_service
from app.main import app
from app.schemas.communication_preferences import (
    CommunicationPreferenceReadResponse,
    CommunicationPreferenceSummary,
    CommunicationPreferenceUpdateRequest,
)
from app.services.auth_service import (
    AuthenticatedSessionContext,
    EmailVerificationRequiredError,
)


class StubCommunicationPreferenceService:
    def __init__(
        self,
        response: CommunicationPreferenceReadResponse | None = None,
    ) -> None:
        self._response = response
        self.updated_calls: list[dict[str, object]] = []

    def describe_contract(self):  # noqa: ANN001
        return {
            "success": True,
            "message": "Communication preferences router registered.",
            "scope": "communication_preferences",
            "guard": "normal_authenticated_verified",
        }

    def get_preferences(self, account_id):  # noqa: ANN001
        if self._response is None:
            from app.services.communication_preference_service import (
                CommunicationPreferenceNotFoundError,
            )

            raise CommunicationPreferenceNotFoundError(f"missing {account_id}")
        return self._response

    def update_preferences(
        self,
        account_id,  # noqa: ANN001
        payload: CommunicationPreferenceUpdateRequest,
    ):
        if self._response is None:
            from app.services.communication_preference_service import (
                CommunicationPreferenceNotFoundError,
            )

            raise CommunicationPreferenceNotFoundError(f"missing {account_id}")
        self.updated_calls.append(
            {
                "account_id": account_id,
                "payload": payload.model_dump(exclude_unset=True),
            }
        )
        return self._response


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
        username="preference-user",
        email="preference-user@example.com",
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


def test_communication_preferences_contract_endpoint_uses_verified_session_guard() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: StubCommunicationPreferenceService()
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.get("/api/v1/communication-preferences/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["communication-preferences-token"]
    assert response.json() == {
        "success": True,
        "message": "Communication preferences router registered.",
        "scope": "communication_preferences",
        "guard": "normal_authenticated_verified",
    }


def test_communication_preferences_contract_endpoint_blocks_pending_verification_context() -> None:
    auth_service = StubAuthService(
        _build_context(status="pending_verification", email_verified_at=None)
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: StubCommunicationPreferenceService()
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.get("/api/v1/communication-preferences/_contract")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "email_verification_required",
            "message": "Email verification is required.",
            "details": {},
        }
    }


def test_communication_preferences_me_endpoint_returns_preference_summary() -> None:
    context = _build_context()
    response_payload = CommunicationPreferenceReadResponse(
        preferences=CommunicationPreferenceSummary(
            account_id=context.account_id,
            marketing_emails_enabled=False,
            product_updates_enabled=True,
            announcement_emails_enabled=True,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: StubCommunicationPreferenceService(response_payload)
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.get("/api/v1/communication-preferences/me")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["communication-preferences-token"]
    assert response.json() == {
        "preferences": {
            "account_id": str(context.account_id),
            "marketing_emails_enabled": False,
            "product_updates_enabled": True,
            "announcement_emails_enabled": True,
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T12:30:00Z",
        }
    }


def test_communication_preferences_me_endpoint_returns_not_found_when_missing() -> None:
    auth_service = StubAuthService(_build_context())
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: StubCommunicationPreferenceService(None)
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.get("/api/v1/communication-preferences/me")
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "communication_preferences_not_found",
            "message": "Communication preferences not found.",
            "details": {},
        }
    }


def test_communication_preferences_patch_me_endpoint_updates_preferences() -> None:
    context = _build_context()
    response_payload = CommunicationPreferenceReadResponse(
        preferences=CommunicationPreferenceSummary(
            account_id=context.account_id,
            marketing_emails_enabled=True,
            product_updates_enabled=False,
            announcement_emails_enabled=True,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
        )
    )
    auth_service = StubAuthService(context)
    preference_service = StubCommunicationPreferenceService(response_payload)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: preference_service
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.patch(
            "/api/v1/communication-preferences/me",
            json={
                "marketing_emails_enabled": True,
                "product_updates_enabled": False,
            },
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert auth_service.received_tokens == ["communication-preferences-token"]
    assert preference_service.updated_calls == [
        {
            "account_id": context.account_id,
            "payload": {
                "marketing_emails_enabled": True,
                "product_updates_enabled": False,
            },
        }
    ]
    assert response.json()["preferences"]["marketing_emails_enabled"] is True
    assert response.json()["preferences"]["product_updates_enabled"] is False


def test_communication_preferences_patch_me_endpoint_rejects_unknown_fields() -> None:
    context = _build_context()
    auth_service = StubAuthService(context)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_communication_preference_service] = (
        lambda: StubCommunicationPreferenceService(
            CommunicationPreferenceReadResponse(
                preferences=CommunicationPreferenceSummary(
                    account_id=context.account_id,
                    marketing_emails_enabled=False,
                    product_updates_enabled=True,
                    announcement_emails_enabled=True,
                    created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
                )
            )
        )
    )

    try:
        client.cookies.set("zeptalytic_session", "communication-preferences-token")
        response = client.patch(
            "/api/v1/communication-preferences/me",
            json={"sms_notifications_enabled": True},
        )
    finally:
        client.cookies.clear()
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
