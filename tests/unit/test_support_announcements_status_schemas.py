from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnnouncementListItem,
    AnnouncementListResponse,
    CursorPageInfo,
    ServiceStatusListItem,
    ServiceStatusListResponse,
    SupportAttachmentMetadataReference,
    SupportAttachmentSummary,
    SupportRouteContractResponse,
    SupportTicketCreateRequest,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    SupportTicketSummary,
)


def test_support_announcement_and_status_schema_exports_are_available() -> None:
    assert SupportTicketCreateRequest is not None
    assert SupportTicketListResponse is not None
    assert AnnouncementListResponse is not None
    assert ServiceStatusListResponse is not None


def test_support_ticket_create_request_forbids_extra_fields_and_limits_attachments() -> None:
    with pytest.raises(ValidationError):
        SupportTicketCreateRequest.model_validate(
            {
                "request_type": "technical_support",
                "related_product_code": "zardbot",
                "priority": "high",
                "subject": "Need help",
                "description": "Launcher is blocked.",
                "attachments": [
                    {
                        "client_reference": f"attachment-{index}",
                        "original_filename": f"log-{index}.txt",
                        "content_type": "text/plain",
                        "file_size_bytes": 64,
                        "upload_token": f"upload-{index}",
                    }
                    for index in range(6)
                ],
                "storage_key": "support/internal-only",
            }
        )


def test_support_ticket_create_request_uses_locked_vocabulary_values() -> None:
    with pytest.raises(ValidationError):
        SupportTicketCreateRequest.model_validate(
            {
                "request_type": "support",
                "priority": "normal",
                "subject": "Need help",
                "description": "Invalid vocabulary should be rejected.",
            }
        )


def test_support_ticket_create_response_and_detail_expose_safe_fields_only() -> None:
    ticket_id = uuid4()
    attachment_id = uuid4()
    created_at = datetime(2026, 4, 19, 1, 0, tzinfo=timezone.utc)
    updated_at = datetime(2026, 4, 19, 1, 5, tzinfo=timezone.utc)
    ticket = SupportTicketSummary(
        ticket_id=ticket_id,
        ticket_code="SUP-2001",
        request_type="billing",
        related_product_code="zepta",
        priority="urgent",
        subject="Charge needs review",
        status="open",
        estimated_response_sla_label="Within 4 hours",
        created_at=created_at,
        updated_at=updated_at,
        attachment_count=1,
    )

    response = SupportTicketCreateResponse(message="Support ticket created.", ticket=ticket)
    detail = SupportTicketDetailResponse(
        ticket=ticket,
        description="The latest invoice looks incorrect.",
        attachments=[
            SupportAttachmentSummary(
                attachment_id=attachment_id,
                original_filename="invoice.pdf",
                content_type="application/pdf",
                file_size_bytes=4096,
                scan_status="pending",
                uploaded_at=created_at,
            )
        ],
    )

    assert response.model_dump(mode="json") == {
        "success": True,
        "message": "Support ticket created.",
        "ticket": {
            "ticket_id": str(ticket_id),
            "ticket_code": "SUP-2001",
            "request_type": "billing",
            "related_product_code": "zepta",
            "priority": "urgent",
            "subject": "Charge needs review",
            "status": "open",
            "estimated_response_sla_label": "Within 4 hours",
            "created_at": "2026-04-19T01:00:00Z",
            "updated_at": "2026-04-19T01:05:00Z",
            "attachment_count": 1,
        },
    }
    assert "storage_key" not in str(detail.model_dump(mode="json"))
    assert "uploaded_by_account_id" not in str(detail.model_dump(mode="json"))


def test_support_ticket_list_response_reuses_cursor_pagination_contract() -> None:
    response = SupportTicketListResponse(
        items=[
            SupportTicketSummary(
                ticket_id=uuid4(),
                ticket_code="SUP-2002",
                request_type="technical_support",
                related_product_code="zardbot",
                priority="high",
                subject="Launcher issue",
                status="in_progress",
                estimated_response_sla_label="Within 1 business day",
                created_at=datetime(2026, 4, 19, 2, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 4, 19, 2, 30, tzinfo=timezone.utc),
                attachment_count=0,
            )
        ],
        page=CursorPageInfo(limit=25, cursor="support_001", next_cursor="support_002"),
    )

    payload = response.model_dump(mode="json")

    assert payload["page"] == {
        "limit": 25,
        "cursor": "support_001",
        "next_cursor": "support_002",
    }


def test_announcement_list_response_reuses_cursor_pagination_contract() -> None:
    announcement_id = uuid4()
    response = AnnouncementListResponse(
        items=[
            AnnouncementListItem(
                announcement_id=announcement_id,
                scope="product",
                product_code="zardbot",
                title="Maintenance window",
                body="Launcher maintenance begins tonight.",
                severity="warning",
                published_at=datetime(2026, 4, 19, 3, 0, tzinfo=timezone.utc),
            )
        ],
        page=CursorPageInfo(limit=10, cursor=None, next_cursor="announcement_002"),
    )

    assert response.model_dump(mode="json") == {
        "items": [
            {
                "announcement_id": str(announcement_id),
                "scope": "product",
                "product_code": "zardbot",
                "title": "Maintenance window",
                "body": "Launcher maintenance begins tonight.",
                "severity": "warning",
                "published_at": "2026-04-19T03:00:00Z",
                "expires_at": None,
            }
        ],
        "page": {
            "limit": 10,
            "cursor": None,
            "next_cursor": "announcement_002",
        },
    }


def test_service_status_response_stays_read_only_and_uses_locked_values() -> None:
    status_id = uuid4()
    response = ServiceStatusListResponse(
        items=[
            ServiceStatusListItem(
                status_id=status_id,
                product_code="zepta",
                status="maintenance",
                message="Scheduled work is in progress.",
                updated_at=datetime(2026, 4, 19, 4, 0, tzinfo=timezone.utc),
            )
        ]
    )

    assert response.model_dump(mode="json") == {
        "items": [
            {
                "status_id": str(status_id),
                "product_code": "zepta",
                "status": "maintenance",
                "message": "Scheduled work is in progress.",
                "updated_at": "2026-04-19T04:00:00Z",
            }
        ]
    }

    with pytest.raises(ValidationError):
        ServiceStatusListItem(
            status_id=uuid4(),
            product_code="zepta",
            status="operational",
            updated_at=datetime(2026, 4, 19, 4, 0, tzinfo=timezone.utc),
        )


def test_support_route_contract_response_extends_shared_mutation_contract() -> None:
    response = SupportRouteContractResponse(
        message="Support route contract is available.",
        action="create_ticket",
    )

    assert response.model_dump(mode="json") == {
        "success": True,
        "message": "Support route contract is available.",
        "action": "create_ticket",
    }


def test_support_attachment_metadata_reference_uses_safe_upload_intent_fields() -> None:
    reference = SupportAttachmentMetadataReference(
        client_reference="attachment-1",
        original_filename="launcher-log.txt",
        content_type="text/plain",
        file_size_bytes=128,
        upload_token="upload-token-1",
    )

    assert reference.model_dump(mode="json") == {
        "client_reference": "attachment-1",
        "original_filename": "launcher-log.txt",
        "content_type": "text/plain",
        "file_size_bytes": 128,
        "upload_token": "upload-token-1",
    }
