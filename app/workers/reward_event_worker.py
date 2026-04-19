from __future__ import annotations

from app.services.reward_event_ingestion_service import (
    RewardEventIngestionCommand,
    RewardEventIngestionResult,
    RewardEventIngestionService,
)


def run_reward_event_ingestion(
    service: RewardEventIngestionService,
    command: RewardEventIngestionCommand,
) -> RewardEventIngestionResult:
    return service.ingest_event(command)
