from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from fastapi import Request

AuditMetadataValue = str | int | float | bool | None

_SENSITIVE_METADATA_KEYS = {
    "body",
    "content",
    "current_password",
    "description",
    "discord_user_id",
    "email",
    "new_password",
    "oauth_code",
    "password",
    "phone",
    "raw_payload",
    "raw_token",
    "recovery_code",
    "secret",
    "subject",
    "token",
}


@dataclass(frozen=True)
class AuditEvent:
    action: str
    outcome: str
    source: str
    occurred_at: datetime
    request_id: str | None
    account_id: str | None
    ip_address: str | None
    metadata: dict[str, AuditMetadataValue] = field(default_factory=dict)

    def to_log_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "outcome": self.outcome,
            "source": self.source,
            "occurred_at": self.occurred_at.isoformat(),
            "request_id": self.request_id,
            "account_id": self.account_id,
            "ip_address": self.ip_address,
            "metadata": self.metadata,
        }


class AuditHook(Protocol):
    def emit(self, event: AuditEvent) -> None:
        ...


class LoggingAuditHook:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("app.audit")

    def emit(self, event: AuditEvent) -> None:
        self._logger.info("audit_event %s", event.to_log_dict())


class InMemoryAuditHook:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


def sanitize_audit_metadata(
    metadata: dict[str, Any] | None,
) -> dict[str, AuditMetadataValue]:
    if not metadata:
        return {}

    sanitized: dict[str, AuditMetadataValue] = {}
    for key, value in metadata.items():
        normalized_key = key.lower()
        if normalized_key in _SENSITIVE_METADATA_KEYS or normalized_key.endswith(
            ("_password", "_token", "_secret")
        ):
            continue

        if isinstance(value, UUID):
            sanitized[key] = str(value)
            continue

        if value is None or isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
            continue

        sanitized[key] = str(value)

    return sanitized


def emit_audit_event(
    audit_hook: AuditHook,
    *,
    request: Request,
    action: str,
    outcome: str,
    account_id: UUID | str | None = None,
    metadata: dict[str, Any] | None = None,
    source: str = "api",
) -> None:
    normalized_account_id = None if account_id is None else str(account_id)
    client_host = request.client.host if request.client is not None else None
    request_id = getattr(request.state, "request_id", None)
    audit_hook.emit(
        AuditEvent(
            action=action,
            outcome=outcome,
            source=source,
            occurred_at=datetime.now(timezone.utc),
            request_id=request_id,
            account_id=normalized_account_id,
            ip_address=client_host,
            metadata=sanitize_audit_metadata(metadata),
        )
    )
