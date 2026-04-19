from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.service_status_repository import ServiceStatusRepository
from app.schemas.service_status import ServiceStatusListItem, ServiceStatusListResponse


class ServiceStatusService:
    def __init__(self, repository: ServiceStatusRepository) -> None:
        self._repository = repository

    def list_current_statuses(
        self,
        *,
        product_codes: list[str] | None = None,
    ) -> ServiceStatusListResponse:
        records = self._repository.list_current_statuses(product_codes=product_codes)
        return ServiceStatusListResponse(
            items=[
                ServiceStatusListItem(
                    status_id=record.status_id,
                    product_code=record.product_code,
                    status=record.status,
                    message=record.message,
                    updated_at=record.updated_at,
                )
                for record in records
            ]
        )


def build_service_status_service(db: Session) -> ServiceStatusService:
    return ServiceStatusService(ServiceStatusRepository(db))
