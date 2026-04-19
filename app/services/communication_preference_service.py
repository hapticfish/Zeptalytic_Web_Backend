from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.communication_preference_repository import (
    CommunicationPreferenceRepository,
)
from app.schemas.communication_preferences import CommunicationPreferenceRouteContractResponse


class CommunicationPreferenceService:
    def __init__(self, repository: CommunicationPreferenceRepository) -> None:
        self._repository = repository

    def describe_contract(self) -> CommunicationPreferenceRouteContractResponse:
        return CommunicationPreferenceRouteContractResponse()


def build_communication_preference_service(
    db: Session,
) -> CommunicationPreferenceService:
    return CommunicationPreferenceService(CommunicationPreferenceRepository(db))
