from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import build_error_response
from app.core.config import settings
from app.db.repositories.email_delivery_event_repository import EmailDeliveryEventRepository
from app.schemas.email import EmailWebhookIngestResponse

router = APIRouter(prefix="/email/webhooks", tags=["email"])

_KNOWN_EVENT_TYPES = {
    "sent": "sent",
    "delivered": "delivered",
    "opened": "opened",
    "open": "opened",
    "clicked": "clicked",
    "click": "clicked",
    "soft_bounce": "soft_bounce",
    "softbounce": "soft_bounce",
    "hard_bounce": "hard_bounce",
    "hardbounce": "hard_bounce",
    "invalid": "invalid_email",
    "invalid_email": "invalid_email",
    "deferred": "deferred",
    "complaint": "complaint",
    "spam": "complaint",
    "unsubscribed": "unsubscribed",
    "blocked": "blocked",
    "error": "error",
}


def _build_webhook_error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    return build_error_response(
        status_code=status_code,
        code=code,
        message=message,
        request_id=getattr(request.state, "request_id", None),
    )


def _normalize_event_type(payload: dict[str, Any]) -> str:
    raw_event = payload.get("event")
    if not isinstance(raw_event, str):
        return "unknown"

    normalized_key = raw_event.strip().lower().replace("-", "_").replace(" ", "_")
    return _KNOWN_EVENT_TYPES.get(normalized_key, "unknown")


def _extract_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_template_id(payload: dict[str, Any]) -> int | None:
    for key in ("templateId", "template_id"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return None


def _extract_event_timestamp(payload: dict[str, Any]) -> datetime | None:
    raw_timestamp = payload.get("date") or payload.get("ts") or payload.get("timestamp")
    if isinstance(raw_timestamp, (int, float)):
        return datetime.fromtimestamp(raw_timestamp, tz=UTC)
    if not isinstance(raw_timestamp, str):
        return None

    candidate = raw_timestamp.strip()
    if not candidate:
        return None

    try:
        if candidate.endswith("Z"):
            return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _build_payload_hash(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def _build_dedupe_key(payload: dict[str, Any]) -> str:
    provider_event_id = _extract_string(payload, "eventId", "event_id", "id")
    if provider_event_id is not None:
        return f"brevo:event:{provider_event_id}"

    event_type = _normalize_event_type(payload)
    provider_message_id = _extract_string(payload, "messageId", "message-id", "message_id")
    email = _extract_string(payload, "email")
    template_id = _extract_template_id(payload)
    event_timestamp = _extract_event_timestamp(payload)

    if provider_message_id is not None:
        timestamp_component = (
            event_timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
            if event_timestamp is not None
            else "none"
        )
        email_component = email or "none"
        template_component = str(template_id) if template_id is not None else "none"
        return (
            "brevo:message:"
            f"{provider_message_id}:{event_type}:{email_component}:{template_component}:{timestamp_component}"
        )

    return f"brevo:payload:{_build_payload_hash(payload)}"


@router.post("/brevo", response_model=EmailWebhookIngestResponse)
async def ingest_brevo_webhook(
    request: Request,
    secret: str | None = None,
    db: Session = Depends(get_db),
) -> EmailWebhookIngestResponse | JSONResponse:
    configured_secret = settings.brevo_webhook_secret
    if not configured_secret or secret != configured_secret:
        return _build_webhook_error(
            request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_webhook_secret",
            message="Webhook authentication failed.",
        )

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _build_webhook_error(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_webhook_payload",
            message="Webhook payload must be valid JSON.",
        )

    if not isinstance(payload, dict):
        return _build_webhook_error(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_webhook_payload",
            message="Webhook payload must be a JSON object.",
        )

    repository = EmailDeliveryEventRepository(db)
    create_result = repository.create_event_if_new(
        provider="brevo",
        event_type=_normalize_event_type(payload),
        dedupe_key=_build_dedupe_key(payload),
        raw_payload=payload,
        provider_message_id=_extract_string(payload, "messageId", "message-id", "message_id"),
        provider_event_id=_extract_string(payload, "eventId", "event_id", "id"),
        email=_extract_string(payload, "email"),
        template_id=_extract_template_id(payload),
        subject=_extract_string(payload, "subject"),
        event_timestamp=_extract_event_timestamp(payload),
    )
    repository.commit()

    if create_result.created:
        return EmailWebhookIngestResponse(status="ok")
    return EmailWebhookIngestResponse(status="duplicate")
