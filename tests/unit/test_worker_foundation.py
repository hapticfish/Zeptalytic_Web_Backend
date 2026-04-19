from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.services.auth_service import StaleSessionCleanupResult
from app.services.pay_projection_service import (
    PayProjectionSnapshot,
    PayProjectionSyncMetadata,
)
from app.services.reward_event_ingestion_service import (
    RewardEventIngestionCommand,
    RewardEventIngestionResult,
)
from app.workers import (
    PayProjectionSyncJob,
    SessionCleanupJob,
    run_pay_projection_sync,
    run_reward_event_ingestion,
    run_session_cleanup,
)


@dataclass
class StubPayProjectionService:
    snapshot: PayProjectionSnapshot

    def __post_init__(self) -> None:
        self.calls: list[UUID] = []

    def refresh_account_snapshot(self, account_id):  # noqa: ANN001
        self.calls.append(account_id)
        return self.snapshot


@dataclass
class StubRewardEventService:
    result: RewardEventIngestionResult

    def __post_init__(self) -> None:
        self.calls: list[RewardEventIngestionCommand] = []

    def ingest_event(self, command: RewardEventIngestionCommand) -> RewardEventIngestionResult:
        self.calls.append(command)
        return self.result


@dataclass
class StubAuthCleanupService:
    result: StaleSessionCleanupResult

    def __post_init__(self) -> None:
        self.calls: list[datetime | None] = []

    def cleanup_stale_sessions(
        self,
        *,
        stale_before: datetime | None = None,
    ) -> StaleSessionCleanupResult:
        self.calls.append(stale_before)
        return self.result


def test_pay_projection_worker_delegates_to_projection_service() -> None:
    account_id = uuid4()
    service = StubPayProjectionService(
        PayProjectionSnapshot(
            account_id=account_id,
            sync=PayProjectionSyncMetadata(pay_status="available", refreshed_from_pay=True),
            subscriptions=[],
            entitlements=[],
            payments=[],
            payment_methods=[],
            product_access_states=[],
        )
    )

    result = run_pay_projection_sync(service, PayProjectionSyncJob(account_id=account_id))

    assert service.calls == [account_id]
    assert result.account_id == account_id
    assert result.pay_status == "available"
    assert result.refreshed_from_pay is True


def test_reward_event_worker_preserves_trusted_ingestion_command() -> None:
    account_id = uuid4()
    command = RewardEventIngestionCommand(
        account_id=account_id,
        event_type="product_usage_confirmed",
        source_type="worker",
        event_id="evt_worker_001",
        source_reference="job/reward-sync/001",
        points_delta=10,
    )
    service = StubRewardEventService(
        RewardEventIngestionResult(
            account_id=account_id,
            event_type=command.event_type,
            source_type=command.source_type,
            source_reference=command.source_reference or command.event_id,
            duplicate=False,
            existing_event=None,
            points_event_id=uuid4(),
            objective_progress=None,
            notification=None,
        )
    )

    result = run_reward_event_ingestion(service, command)

    assert service.calls == [command]
    assert result.account_id == account_id
    assert result.duplicate is False


def test_session_cleanup_worker_delegates_cutoff_to_auth_service() -> None:
    cutoff = datetime(2026, 4, 19, 15, 0, tzinfo=timezone.utc)
    service = StubAuthCleanupService(
        StaleSessionCleanupResult(deleted_session_count=3, stale_before=cutoff)
    )

    result = run_session_cleanup(service, SessionCleanupJob(stale_before=cutoff))

    assert service.calls == [cutoff]
    assert result.deleted_session_count == 3
    assert result.stale_before == cutoff
