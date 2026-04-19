from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.service_statuses import ServiceStatus


@dataclass(slots=True)
class ServiceStatusRecord:
    status_id: UUID
    product_code: str
    status: str
    message: str | None
    updated_at: datetime


class ServiceStatusRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_current_statuses(self, *, product_codes: list[str] | None = None) -> list[ServiceStatusRecord]:
        statement = select(ServiceStatus).order_by(
            ServiceStatus.product_code.asc(),
            ServiceStatus.updated_at.desc(),
            ServiceStatus.id.desc(),
        )
        if product_codes:
            statement = statement.where(ServiceStatus.product_code.in_(product_codes))

        rows = self._db.scalars(statement).all()
        current_by_product: dict[str, ServiceStatusRecord] = {}
        for row in rows:
            if row.product_code in current_by_product:
                continue
            current_by_product[row.product_code] = self._to_record(row)
        return list(current_by_product.values())

    @staticmethod
    def _to_record(row: ServiceStatus) -> ServiceStatusRecord:
        return ServiceStatusRecord(
            status_id=row.id,
            product_code=row.product_code,
            status=row.status,
            message=row.message,
            updated_at=row.updated_at,
        )
