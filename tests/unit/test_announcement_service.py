from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.announcement_repository import AnnouncementRecord
from app.services.announcement_service import AnnouncementService


@dataclass
class StubAnnouncementRepository:
    records: list[AnnouncementRecord]

    def __post_init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_active_announcements(
        self,
        *,
        product_codes: list[str] | None = None,
        limit: int = 10,
        now: datetime | None = None,
    ) -> list[AnnouncementRecord]:
        self.calls.append(
            {
                "product_codes": product_codes,
                "limit": limit,
                "now": now,
            }
        )
        return self.records[:limit]


def test_announcement_service_returns_safe_dtos_with_product_filtering() -> None:
    now = datetime(2026, 4, 19, 8, 0, tzinfo=timezone.utc)
    repository = StubAnnouncementRepository(
        records=[
            AnnouncementRecord(
                announcement_id=uuid4(),
                scope="product",
                product_code="zardbot",
                title="ZardBot maintenance",
                body="Maintenance starts tonight.",
                severity="warning",
                published_at=now,
                expires_at=None,
                created_at=now,
                updated_at=now,
            )
        ]
    )
    service = AnnouncementService(repository)

    response = service.list_announcements(product_codes=["zardbot"], limit=5, now=now)

    assert repository.calls == [
        {
            "product_codes": ["zardbot"],
            "limit": 5,
            "now": now,
        }
    ]
    assert response.page.limit == 5
    assert response.page.cursor is None
    assert response.page.next_cursor is None
    assert len(response.items) == 1
    assert response.items[0].product_code == "zardbot"
    assert response.items[0].severity == "warning"


def test_announcement_service_clamps_limit_to_maximum() -> None:
    repository = StubAnnouncementRepository(records=[])
    service = AnnouncementService(repository)

    response = service.list_announcements(limit=1000)

    assert repository.calls[0]["limit"] == 100
    assert response.page.limit == 100
