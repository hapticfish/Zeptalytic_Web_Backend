from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services.auth_service import AuthService, StaleSessionCleanupResult


@dataclass(slots=True)
class SessionCleanupJob:
    stale_before: datetime | None = None


def run_session_cleanup(
    service: AuthService,
    job: SessionCleanupJob | None = None,
) -> StaleSessionCleanupResult:
    cleanup_job = job or SessionCleanupJob()
    return service.cleanup_stale_sessions(stale_before=cleanup_job.stale_before)
