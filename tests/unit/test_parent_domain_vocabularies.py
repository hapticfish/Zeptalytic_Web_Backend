from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import Boolean, String

from app.db.models.accounts import Account
from app.db.models.addresses import Address
from app.db.models.announcements import Announcement
from app.db.models.entitlement_summaries import EntitlementSummary
from app.db.models.oauth_connections import OAuthConnection
from app.db.models.payment_method_summaries import PaymentMethodSummary
from app.db.models.payment_summaries import PaymentSummary
from app.db.models.product_access_states import ProductAccessState
from app.db.models.service_statuses import ServiceStatus
from app.db.models.subscription_summaries import SubscriptionSummary
from app.db.models.support_ticket_attachments import SupportTicketAttachment
from app.db.models.support_ticket_messages import SupportTicketMessage
from app.db.models.support_tickets import SupportTicket
from app.db.vocabularies import ACCOUNT_STATUS
from app.db.vocabularies import ANNOUNCEMENT_SCOPE
from app.db.vocabularies import ANNOUNCEMENT_SEVERITY
from app.db.vocabularies import ATTACHMENT_SCAN_STATUS
from app.db.vocabularies import BILLING_INTERVAL
from app.db.vocabularies import INITIAL_ADDRESS_TYPE
from app.db.vocabularies import LAUNCHER_ACCESS_STATE
from app.db.vocabularies import LockedVocabulary
from app.db.vocabularies import NORMALIZED_ENTITLEMENT_STATUS
from app.db.vocabularies import NORMALIZED_PAYMENT_STATUS
from app.db.vocabularies import NORMALIZED_SUBSCRIPTION_STATUS
from app.db.vocabularies import OAUTH_INTEGRATION_STATUS
from app.db.vocabularies import PARENT_ACCOUNT_ROLE
from app.db.vocabularies import PAYMENT_METHOD_SUMMARY_STATUS
from app.db.vocabularies import PAYMENT_RAIL
from app.db.vocabularies import SERVICE_STATUS
from app.db.vocabularies import SUPPORT_MESSAGE_AUTHOR_TYPE
from app.db.vocabularies import SUPPORT_PRIORITY
from app.db.vocabularies import SUPPORT_REQUEST_TYPE
from app.db.vocabularies import SUPPORT_TICKET_STATUS


REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_RECORD_PATH = REPO_ROOT / "docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md"

IMPLEMENTED_PARENT_VOCABULARIES: dict[str, LockedVocabulary] = {
    "Account status": ACCOUNT_STATUS,
    "Parent account role": PARENT_ACCOUNT_ROLE,
    "Announcement scope": ANNOUNCEMENT_SCOPE,
    "Announcement severity": ANNOUNCEMENT_SEVERITY,
    "Service status": SERVICE_STATUS,
    "Billing interval": BILLING_INTERVAL,
    "Normalized subscription status": NORMALIZED_SUBSCRIPTION_STATUS,
    "Normalized entitlement status": NORMALIZED_ENTITLEMENT_STATUS,
    "Launcher access state": LAUNCHER_ACCESS_STATE,
    "Payment rail": PAYMENT_RAIL,
    "Normalized payment status": NORMALIZED_PAYMENT_STATUS,
    "Payment-method summary status": PAYMENT_METHOD_SUMMARY_STATUS,
    "OAuth / integration status": OAUTH_INTEGRATION_STATUS,
    "Initial address type": INITIAL_ADDRESS_TYPE,
    "Support request type": SUPPORT_REQUEST_TYPE,
    "Support priority": SUPPORT_PRIORITY,
    "Support ticket status": SUPPORT_TICKET_STATUS,
    "Support message author type": SUPPORT_MESSAGE_AUTHOR_TYPE,
    "Attachment scan status": ATTACHMENT_SCAN_STATUS,
}

MODEL_VOCABULARY_COLUMNS = (
    (Account, "status"),
    (Account, "role"),
    (Announcement, "scope"),
    (Announcement, "severity"),
    (ServiceStatus, "status"),
    (SubscriptionSummary, "billing_interval"),
    (SubscriptionSummary, "normalized_status"),
    (EntitlementSummary, "status"),
    (ProductAccessState, "access_state"),
    (PaymentSummary, "payment_rail"),
    (PaymentSummary, "normalized_status"),
    (PaymentMethodSummary, "status"),
    (OAuthConnection, "status"),
    (Address, "address_type"),
    (SupportTicket, "request_type"),
    (SupportTicket, "priority"),
    (SupportTicket, "status"),
    (SupportTicketMessage, "author_type"),
    (SupportTicketAttachment, "scan_status"),
)


def _parse_locked_vocabularies() -> dict[str, LockedVocabulary]:
    content = VOCABULARY_RECORD_PATH.read_text(encoding="utf-8")
    sections = re.findall(
        r"## \d+\. (?P<title>.+?)\n(?P<body>.*?)(?=\n## \d+\. |\n## [A-Z]|\Z)",
        content,
        flags=re.DOTALL,
    )

    parsed: dict[str, LockedVocabulary] = {}
    for title, body in sections:
        if "- Allowed values:" not in body:
            continue

        values_block = body.split("- Allowed values:\n", maxsplit=1)[1].split("- Default:\n", maxsplit=1)[0]
        values = tuple(re.findall(r"  - `([^`]+)`", values_block))

        default_match = re.search(r"- Default:\n  - `([^`]+)`", body)
        no_default_match = re.search(r"- Default:\n  - none", body)
        default = default_match.group(1) if default_match else None

        assert default_match or no_default_match, f"Missing default declaration for {title}"

        parsed[title] = LockedVocabulary(allowed_values=values, default=default)

    return parsed


def test_implemented_parent_vocabularies_match_decision_record() -> None:
    parsed_vocabularies = _parse_locked_vocabularies()

    assert IMPLEMENTED_PARENT_VOCABULARIES == parsed_vocabularies


def test_parent_model_vocabulary_columns_use_expected_string_shape() -> None:
    for model, column_name in MODEL_VOCABULARY_COLUMNS:
        column = model.__table__.c[column_name]

        assert isinstance(column.type, String)
        assert column.type.length == 32
        assert not column.nullable


def test_payment_method_summary_keeps_separate_default_flag_from_status_vocabulary() -> None:
    is_default_column = PaymentMethodSummary.__table__.c["is_default"]
    status_column = PaymentMethodSummary.__table__.c["status"]

    assert isinstance(is_default_column.type, Boolean)
    assert not is_default_column.nullable
    assert status_column.name == "status"
