from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.service_status_repository import ServiceStatusRecord
from app.services.service_status_service import ServiceStatusService


@dataclass
class StubServiceStatusRepository:
    records: list[ServiceStatusRecord]

    def __post_init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_current_statuses(
        self,
        *,
        product_codes: list[str] | None = None,
    ) -> list[ServiceStatusRecord]:
        self.calls.append({"product_codes": product_codes})
        return self.records


def test_service_status_service_returns_current_product_statuses() -> None:
    updated_at = datetime(2026, 4, 19, 8, 30, tzinfo=timezone.utc)
    repository = StubServiceStatusRepository(
        records=[
            ServiceStatusRecord(
                status_id=uuid4(),
                product_code="zardbot",
                status="degraded",
                message="Intermittent launcher delay.",
                updated_at=updated_at,
            )
        ]
    )
    service = ServiceStatusService(repository)

    response = service.list_current_statuses(product_codes=["zardbot"])

    assert repository.calls == [{"product_codes": ["zardbot"]}]
    assert len(response.items) == 1
    assert response.items[0].status == "degraded"
    assert response.items[0].message == "Intermittent launcher delay."


def test_service_status_service_returns_empty_list_when_repository_has_no_rows() -> None:
    repository = StubServiceStatusRepository(records=[])
    service = ServiceStatusService(repository)

    response = service.list_current_statuses()

    assert response.items == []
