from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.db.repositories.support_repository import (
    SupportAttachmentCreateInput,
    SupportAttachmentRecord,
    SupportTicketDetailRecord,
    SupportTicketRecord,
)
from app.schemas.support import SupportAttachmentMetadataReference, SupportTicketCreateRequest
from app.services.auth_service import AuthenticatedSessionContext
from app.services.support_service import (
    SupportAccessRestrictedError,
    SupportService,
    SupportTicketNotFoundError,
    SupportTicketValidationError,
)


@dataclass
class StubUnitOfWork:
    commits: int = 0
    rollbacks: int = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class StubSupportRepository:
    def __init__(
        self,
        *,
        created_detail: SupportTicketDetailRecord | None = None,
        listed_tickets: list[SupportTicketRecord] | None = None,
        detail_record: SupportTicketDetailRecord | None = None,
        existing_ticket_codes: set[str] | None = None,
    ) -> None:
        self._created_detail = created_detail
        self._listed_tickets = listed_tickets or []
        self._detail_record = detail_record
        self._existing_ticket_codes = existing_ticket_codes or set()
        self.create_calls: list[dict[str, object]] = []
        self.list_calls: list[dict[str, object]] = []
        self.detail_calls: list[dict[str, object]] = []
        self.unit_of_work = StubUnitOfWork()

    def commit(self) -> None:
        self.unit_of_work.commit()

    def rollback(self) -> None:
        self.unit_of_work.rollback()

    def ticket_code_exists(self, ticket_code: str) -> bool:
        return ticket_code in self._existing_ticket_codes

    def create_ticket(
        self,
        *,
        account_id,
        ticket_code: str,
        request_type: str,
        related_product_code: str | None,
        priority: str,
        subject: str,
        description: str,
        status: str,
        estimated_response_sla_label: str | None,
        initial_message_author_type: str,
        initial_message_body: str,
        attachments: list[SupportAttachmentCreateInput],
    ) -> SupportTicketDetailRecord:
        self.create_calls.append(
            {
                "account_id": account_id,
                "ticket_code": ticket_code,
                "request_type": request_type,
                "related_product_code": related_product_code,
                "priority": priority,
                "subject": subject,
                "description": description,
                "status": status,
                "estimated_response_sla_label": estimated_response_sla_label,
                "initial_message_author_type": initial_message_author_type,
                "initial_message_body": initial_message_body,
                "attachments": attachments,
            }
        )
        if self._created_detail is None:
            raise AssertionError("Expected created support ticket detail.")
        return self._created_detail

    def list_tickets_for_account(
        self,
        account_id,
        *,
        limit: int,
        created_before,
        ticket_id_before,
    ) -> list[SupportTicketRecord]:
        self.list_calls.append(
            {
                "account_id": account_id,
                "limit": limit,
                "created_before": created_before,
                "ticket_id_before": ticket_id_before,
            }
        )
        return self._listed_tickets

    def get_ticket_detail_for_account(self, account_id, ticket_id):
        self.detail_calls.append({"account_id": account_id, "ticket_id": ticket_id})
        return self._detail_record


def _build_context(*, status: str = "active") -> AuthenticatedSessionContext:
    return AuthenticatedSessionContext(
        session_id=uuid4(),
        account_id=uuid4(),
        username="support-user",
        email="support-user@example.com",
        status=status,
        role="user",
        email_verified_at=datetime(2026, 4, 18, 10, 0, tzinfo=timezone.utc),
        session_created_at=datetime(2026, 4, 18, 10, 0, tzinfo=timezone.utc),
        session_expires_at=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
        session_revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest",
        two_factor_enabled=False,
        two_factor_method=None,
        recovery_methods_available_count=0,
        recovery_codes_generated_at=None,
    )


def _build_ticket_record(*, account_id=None, ticket_id=None, ticket_code: str = "SUP-2001") -> SupportTicketRecord:
    return SupportTicketRecord(
        ticket_id=ticket_id or uuid4(),
        account_id=account_id or uuid4(),
        ticket_code=ticket_code,
        request_type="technical_support",
        related_product_code="zardbot",
        priority="high",
        subject="Launcher issue",
        description="Launcher crashes when opening.",
        status="open",
        estimated_response_sla_label="Estimated response: within 8 business hours.",
        created_at=datetime(2026, 4, 18, 14, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 18, 14, 5, tzinfo=timezone.utc),
        attachment_count=1,
    )


def _build_detail_record(*, account_id=None, ticket_id=None) -> SupportTicketDetailRecord:
    ticket = _build_ticket_record(account_id=account_id, ticket_id=ticket_id)
    return SupportTicketDetailRecord(
        ticket=ticket,
        attachments=[
            SupportAttachmentRecord(
                attachment_id=uuid4(),
                ticket_id=ticket.ticket_id,
                uploaded_by_account_id=ticket.account_id,
                storage_key=f"support/{ticket.ticket_code}/attachment-1/error-log.txt",
                original_filename="error-log.txt",
                content_type="text/plain",
                file_size_bytes=512,
                scan_status="pending",
                created_at=datetime(2026, 4, 18, 14, 1, tzinfo=timezone.utc),
            )
        ],
    )


def test_support_service_creates_ticket_with_defaults_and_commits() -> None:
    context = _build_context()
    created_detail = _build_detail_record(account_id=context.account_id)
    repository = StubSupportRepository(created_detail=created_detail)
    service = SupportService(repository)

    response = service.create_ticket(
        context,
        SupportTicketCreateRequest(
            request_type="technical_support",
            related_product_code="zardbot",
            priority="high",
            subject=" Launcher issue ",
            description=" Launcher crashes when opening. ",
            attachments=[
                SupportAttachmentMetadataReference(
                    client_reference="attachment-1",
                    original_filename="error-log.txt",
                    content_type="text/plain",
                    file_size_bytes=512,
                    upload_token="upload-token-1",
                )
            ],
        ),
    )

    assert len(repository.create_calls) == 1
    create_call = repository.create_calls[0]
    assert create_call["account_id"] == context.account_id
    assert str(create_call["ticket_code"]).startswith("SUP-")
    assert create_call["status"] == "open"
    assert create_call["initial_message_author_type"] == "customer"
    assert create_call["initial_message_body"] == "Launcher crashes when opening."
    assert create_call["estimated_response_sla_label"] == "Estimated response: within 8 business hours."
    stored_attachments = create_call["attachments"]
    assert isinstance(stored_attachments, list)
    assert len(stored_attachments) == 1
    assert stored_attachments[0].scan_status == "pending"
    assert str(create_call["ticket_code"]) in stored_attachments[0].storage_key
    assert repository.unit_of_work.commits == 1
    assert repository.unit_of_work.rollbacks == 0
    assert response.ticket.ticket_code == created_detail.ticket.ticket_code


def test_support_service_rejects_duplicate_attachment_upload_tokens() -> None:
    context = _build_context()
    repository = StubSupportRepository(created_detail=_build_detail_record(account_id=context.account_id))
    service = SupportService(repository)

    try:
        service.create_ticket(
            context,
            SupportTicketCreateRequest(
                request_type="billing",
                related_product_code="zardbot",
                priority="medium",
                subject="Need invoice help",
                description="Invoice copy missing.",
                attachments=[
                    SupportAttachmentMetadataReference(
                        client_reference="attachment-1",
                        original_filename="invoice.pdf",
                        content_type="application/pdf",
                        file_size_bytes=1024,
                        upload_token="duplicate-token",
                    ),
                    SupportAttachmentMetadataReference(
                        client_reference="attachment-2",
                        original_filename="invoice-copy.pdf",
                        content_type="application/pdf",
                        file_size_bytes=2048,
                        upload_token="duplicate-token",
                    ),
                ],
            ),
        )
    except SupportTicketValidationError:
        pass
    else:
        raise AssertionError("Expected duplicate upload tokens to raise SupportTicketValidationError")

    assert repository.create_calls == []
    assert repository.unit_of_work.commits == 0
    assert repository.unit_of_work.rollbacks == 0


def test_support_service_rejects_blank_subject_or_description() -> None:
    context = _build_context()
    repository = StubSupportRepository(created_detail=_build_detail_record(account_id=context.account_id))
    service = SupportService(repository)
    invalid_payload = SupportTicketCreateRequest.model_construct(
        request_type="technical_support",
        related_product_code="zardbot",
        priority="medium",
        subject="   ",
        description="   ",
        attachments=[],
    )

    try:
        service.create_ticket(context, invalid_payload)
    except SupportTicketValidationError:
        pass
    else:
        raise AssertionError("Expected blank payload values to raise SupportTicketValidationError")

    assert repository.create_calls == []


def test_support_service_lists_and_reads_account_scoped_tickets() -> None:
    context = _build_context(status="suspended")
    ticket_id = uuid4()
    listed_record = _build_ticket_record(account_id=context.account_id, ticket_id=ticket_id)
    detail_record = _build_detail_record(account_id=context.account_id, ticket_id=ticket_id)
    repository = StubSupportRepository(
        listed_tickets=[listed_record],
        detail_record=detail_record,
    )
    service = SupportService(repository)

    list_response = service.list_tickets(context, limit=1)
    detail_response = service.get_ticket_detail(context, ticket_id)

    assert repository.list_calls == [
        {
            "account_id": context.account_id,
            "limit": 2,
            "created_before": None,
            "ticket_id_before": None,
        }
    ]
    assert repository.detail_calls == [{"account_id": context.account_id, "ticket_id": ticket_id}]
    assert list_response.items[0].ticket_id == ticket_id
    assert detail_response.ticket.ticket_id == ticket_id
    assert detail_response.attachments[0].original_filename == "error-log.txt"


def test_support_service_blocks_closed_accounts() -> None:
    context = _build_context(status="closed")
    repository = StubSupportRepository(created_detail=_build_detail_record(account_id=context.account_id))
    service = SupportService(repository)

    try:
        service.list_tickets(context)
    except SupportAccessRestrictedError as exc:
        assert exc.status == "closed"
    else:
        raise AssertionError("Expected closed accounts to be blocked from support access")


def test_support_service_raises_not_found_for_missing_ticket_detail() -> None:
    context = _build_context()
    repository = StubSupportRepository(detail_record=None)
    service = SupportService(repository)

    try:
        service.get_ticket_detail(context, uuid4())
    except SupportTicketNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing support ticket detail to raise SupportTicketNotFoundError")
