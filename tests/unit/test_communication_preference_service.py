from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.communication_preferences import CommunicationPreferenceUpdateRequest
from app.services.communication_preference_service import (
    CommunicationPreferenceNotFoundError,
    CommunicationPreferenceService,
    CommunicationPreferenceUpdateValidationError,
)


@dataclass
class StubCommunicationPreferenceRecord:
    account_id: object
    marketing_emails_enabled: bool
    product_updates_enabled: bool
    announcement_emails_enabled: bool
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


class StubCommunicationPreferenceRepository:
    def __init__(self, record: StubCommunicationPreferenceRecord | None) -> None:
        self._record = record
        self.received_account_ids: list[object] = []
        self.updated_calls: list[dict[str, object]] = []
        self.unit_of_work = StubUnitOfWork()

    def get_for_account(self, account_id):  # noqa: ANN001
        self.received_account_ids.append(account_id)
        return self._record

    def update_for_account(
        self,
        account_id,  # noqa: ANN001
        *,
        updates: dict[str, bool],
    ):
        self.updated_calls.append({"account_id": account_id, "updates": updates})
        return self._record

    def commit(self) -> None:
        self.unit_of_work.commit()

    def rollback(self) -> None:
        self.unit_of_work.rollback()


def test_communication_preference_service_builds_safe_read_response() -> None:
    account_id = uuid4()
    repository = StubCommunicationPreferenceRepository(
        StubCommunicationPreferenceRecord(
            account_id=account_id,
            marketing_emails_enabled=False,
            product_updates_enabled=True,
            announcement_emails_enabled=True,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 12, 30, tzinfo=timezone.utc),
        )
    )
    service = CommunicationPreferenceService(repository)

    response = service.get_preferences(account_id)

    assert repository.received_account_ids == [account_id]
    assert response.model_dump(mode="json") == {
        "preferences": {
            "account_id": str(account_id),
            "marketing_emails_enabled": False,
            "product_updates_enabled": True,
            "announcement_emails_enabled": True,
            "created_at": "2026-04-18T12:00:00Z",
            "updated_at": "2026-04-18T12:30:00Z",
        }
    }


def test_communication_preference_service_updates_existing_flags() -> None:
    account_id = uuid4()
    repository = StubCommunicationPreferenceRepository(
        StubCommunicationPreferenceRecord(
            account_id=account_id,
            marketing_emails_enabled=True,
            product_updates_enabled=False,
            announcement_emails_enabled=True,
            created_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 18, 13, 0, tzinfo=timezone.utc),
        )
    )
    service = CommunicationPreferenceService(repository)

    response = service.update_preferences(
        account_id,
        CommunicationPreferenceUpdateRequest(
            marketing_emails_enabled=True,
            product_updates_enabled=False,
        ),
    )

    assert repository.updated_calls == [
        {
            "account_id": account_id,
            "updates": {
                "marketing_emails_enabled": True,
                "product_updates_enabled": False,
            },
        }
    ]
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.preferences.marketing_emails_enabled is True
    assert response.preferences.product_updates_enabled is False


def test_communication_preference_service_rejects_empty_update_payload() -> None:
    repository = StubCommunicationPreferenceRepository(None)
    service = CommunicationPreferenceService(repository)

    try:
        service.update_preferences(uuid4(), CommunicationPreferenceUpdateRequest())
    except CommunicationPreferenceUpdateValidationError:
        pass
    else:
        raise AssertionError(
            "Expected empty update payload to raise CommunicationPreferenceUpdateValidationError"
        )


def test_communication_preference_service_raises_not_found_for_missing_record() -> None:
    repository = StubCommunicationPreferenceRepository(None)
    service = CommunicationPreferenceService(repository)

    try:
        service.get_preferences(uuid4())
    except CommunicationPreferenceNotFoundError:
        pass
    else:
        raise AssertionError(
            "Expected missing communication preferences to raise CommunicationPreferenceNotFoundError"
        )
