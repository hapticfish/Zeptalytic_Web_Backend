from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.communication_preference_repository import (
    CommunicationPreferenceRepository,
)
from app.schemas.communication_preferences import (
    CommunicationPreferenceReadResponse,
    CommunicationPreferenceRouteContractResponse,
    CommunicationPreferenceSummary,
    CommunicationPreferenceUpdateRequest,
)


class CommunicationPreferenceNotFoundError(Exception):
    """Raised when communication preferences are missing for an account."""


class CommunicationPreferenceUpdateValidationError(Exception):
    """Raised when a communication preference update request is invalid."""


class CommunicationPreferenceService:
    def __init__(self, repository: CommunicationPreferenceRepository) -> None:
        self._repository = repository

    def describe_contract(self) -> CommunicationPreferenceRouteContractResponse:
        return CommunicationPreferenceRouteContractResponse()

    def get_preferences(self, account_id) -> CommunicationPreferenceReadResponse:  # noqa: ANN001
        record = self._repository.get_for_account(account_id)
        if record is None:
            raise CommunicationPreferenceNotFoundError(
                f"No communication preferences exist for account {account_id}"
            )
        return self._build_read_response(record)

    def update_preferences(
        self,
        account_id,
        payload: CommunicationPreferenceUpdateRequest,  # noqa: ANN001
    ) -> CommunicationPreferenceReadResponse:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise CommunicationPreferenceUpdateValidationError(
                "At least one communication preference field must be provided."
            )

        record = self._repository.update_for_account(account_id, updates=updates)
        if record is None:
            self._repository.rollback()
            raise CommunicationPreferenceNotFoundError(
                f"No communication preferences exist for account {account_id}"
            )

        self._repository.commit()
        return self._build_read_response(record)

    @staticmethod
    def _build_read_response(record) -> CommunicationPreferenceReadResponse:  # noqa: ANN001
        return CommunicationPreferenceReadResponse(
            preferences=CommunicationPreferenceSummary(
                account_id=record.account_id,
                marketing_emails_enabled=record.marketing_emails_enabled,
                product_updates_enabled=record.product_updates_enabled,
                announcement_emails_enabled=record.announcement_emails_enabled,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
        )


def build_communication_preference_service(
    db: Session,
) -> CommunicationPreferenceService:
    return CommunicationPreferenceService(CommunicationPreferenceRepository(db))
