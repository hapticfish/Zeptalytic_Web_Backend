"""Shared utilities."""

from app.utils.audit import (
    AuditEvent,
    AuditHook,
    InMemoryAuditHook,
    LoggingAuditHook,
    emit_audit_event,
    sanitize_audit_metadata,
)
from app.utils.request_id import REQUEST_ID_HEADER_NAME, build_request_id, register_request_id_middleware
from app.utils.rate_limits import (
    InMemoryRateLimiter,
    RateLimitExceededError,
    RateLimitPolicy,
    build_authenticated_rate_limit_key,
    build_auth_rate_limit_policy,
    build_billing_action_rate_limit_policy,
    build_discord_callback_rate_limit_policy,
    build_request_rate_limit_key,
    build_support_ticket_rate_limit_policy,
)

__all__ = [
    "AuditEvent",
    "AuditHook",
    "InMemoryAuditHook",
    "LoggingAuditHook",
    "REQUEST_ID_HEADER_NAME",
    "InMemoryRateLimiter",
    "RateLimitExceededError",
    "RateLimitPolicy",
    "build_request_id",
    "build_authenticated_rate_limit_key",
    "build_auth_rate_limit_policy",
    "build_billing_action_rate_limit_policy",
    "build_discord_callback_rate_limit_policy",
    "build_request_rate_limit_key",
    "build_support_ticket_rate_limit_policy",
    "emit_audit_event",
    "register_request_id_middleware",
    "sanitize_audit_metadata",
]
