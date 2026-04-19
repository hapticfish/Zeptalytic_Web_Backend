from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.services.pay_projection_service import PayProjectionService


@dataclass(slots=True)
class PayProjectionSyncJob:
    account_id: UUID


@dataclass(slots=True)
class PayProjectionSyncResult:
    account_id: UUID
    pay_status: str
    refreshed_from_pay: bool


def run_pay_projection_sync(
    service: PayProjectionService,
    job: PayProjectionSyncJob,
) -> PayProjectionSyncResult:
    snapshot = service.refresh_account_snapshot(job.account_id)
    return PayProjectionSyncResult(
        account_id=snapshot.account_id,
        pay_status=snapshot.sync.pay_status,
        refreshed_from_pay=snapshot.sync.refreshed_from_pay,
    )
