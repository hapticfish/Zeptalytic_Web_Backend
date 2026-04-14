from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockedVocabulary:
    allowed_values: tuple[str, ...]
    default: str | None


ACCOUNT_STATUS = LockedVocabulary(
    allowed_values=("active", "pending_verification", "suspended", "closed"),
    default="pending_verification",
)

PARENT_ACCOUNT_ROLE = LockedVocabulary(
    allowed_values=("user", "admin", "super_admin"),
    default="user",
)

ANNOUNCEMENT_SCOPE = LockedVocabulary(
    allowed_values=("global", "product"),
    default="global",
)

ANNOUNCEMENT_SEVERITY = LockedVocabulary(
    allowed_values=("info", "success", "warning", "critical"),
    default="info",
)

SERVICE_STATUS = LockedVocabulary(
    allowed_values=("online", "degraded", "maintenance", "offline"),
    default="online",
)

BILLING_INTERVAL = LockedVocabulary(
    allowed_values=("MONTHLY", "ANNUAL"),
    default="MONTHLY",
)

NORMALIZED_SUBSCRIPTION_STATUS = LockedVocabulary(
    allowed_values=(
        "active",
        "trialing",
        "past_due",
        "paused",
        "cancel_at_period_end",
        "canceled",
        "incomplete",
        "incomplete_expired",
        "unpaid",
        "suspended",
    ),
    default="incomplete",
)

NORMALIZED_ENTITLEMENT_STATUS = LockedVocabulary(
    allowed_values=("OFF", "ON", "PAUSED", "SCHEDULED_OFF", "BLOCKED_COMPLIANCE"),
    default="OFF",
)

LAUNCHER_ACCESS_STATE = LockedVocabulary(
    allowed_values=("none", "provision_pending", "active", "suspended"),
    default="none",
)

PAYMENT_RAIL = LockedVocabulary(
    allowed_values=("STRIPE", "COINBASE_COMMERCE"),
    default=None,
)

NORMALIZED_PAYMENT_STATUS = LockedVocabulary(
    allowed_values=(
        "INITIATED",
        "REQUIRES_ACTION",
        "SUCCEEDED",
        "FAILED",
        "REFUNDED",
        "DISPUTED",
        "CHARGE_CREATED",
        "PENDING_ONCHAIN",
        "CONFIRMED_FINAL",
        "EXPIRED",
        "UNDERPAID_REVIEW",
        "OVERPAID_REVIEW",
    ),
    default="INITIATED",
)

PAYMENT_METHOD_SUMMARY_STATUS = LockedVocabulary(
    allowed_values=("active", "default", "expired", "disabled"),
    default="active",
)

OAUTH_INTEGRATION_STATUS = LockedVocabulary(
    allowed_values=("connected", "disconnected", "error", "pending"),
    default="pending",
)

INITIAL_ADDRESS_TYPE = LockedVocabulary(
    allowed_values=("billing", "shipping"),
    default="billing",
)

SUPPORT_REQUEST_TYPE = LockedVocabulary(
    allowed_values=("billing", "sales", "feature_request", "technical_support"),
    default="technical_support",
)

SUPPORT_PRIORITY = LockedVocabulary(
    allowed_values=("low", "medium", "high", "urgent"),
    default="medium",
)

SUPPORT_TICKET_STATUS = LockedVocabulary(
    allowed_values=("open", "in_progress", "waiting_on_customer", "resolved", "closed"),
    default="open",
)

SUPPORT_MESSAGE_AUTHOR_TYPE = LockedVocabulary(
    allowed_values=("customer", "support_agent", "system"),
    default="customer",
)

ATTACHMENT_SCAN_STATUS = LockedVocabulary(
    allowed_values=("pending", "clean", "infected", "failed"),
    default="pending",
)
