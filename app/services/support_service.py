from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.repositories.support_repository import (
    SupportAttachmentCreateInput,
    SupportAttachmentRecord,
    SupportRepository,
    SupportTicketDetailRecord,
    SupportTicketRecord,
)
from app.db.vocabularies import (
    ATTACHMENT_SCAN_STATUS,
    SUPPORT_MESSAGE_AUTHOR_TYPE,
    SUPPORT_PRIORITY,
    SUPPORT_REQUEST_TYPE,
    SUPPORT_TICKET_STATUS,
)
from app.schemas.common import CursorPageInfo
from app.schemas.support import (
    SupportAttachmentMetadataReference,
    SupportAttachmentSummary,
    SupportTicketCreateRequest,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    SupportTicketSummary,
)
from app.services.auth_service import AuthenticatedSessionContext

DEFAULT_TICKET_PREFIX = "SUP"
DEFAULT_CURSOR_LIMIT = 25
MAX_CURSOR_LIMIT = 100
ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".csv",
    ".docx",
    ".jpeg",
    ".jpg",
    ".log",
    ".pdf",
    ".png",
    ".txt",
}
PRIORITY_SLA_LABELS = {
    "low": "Estimated response: within 3 business days.",
    "medium": "Estimated response: within 1 business day.",
    "high": "Estimated response: within 8 business hours.",
    "urgent": "Estimated response: within 4 business hours.",
}
DEFAULT_SLA_LABEL = "Estimated response: support will review your request soon."


@dataclass(slots=True)
class PlannedSupportAttachment:
    original_filename: str
    content_type: str
    file_size_bytes: int
    scan_status: str
    storage_key: str


class SupportAttachmentStoragePlanner(Protocol):
    def build_storage_key(
        self,
        *,
        ticket_code: str,
        attachment: SupportAttachmentMetadataReference,
    ) -> str: ...


class DefaultSupportAttachmentStoragePlanner:
    def build_storage_key(
        self,
        *,
        ticket_code: str,
        attachment: SupportAttachmentMetadataReference,
    ) -> str:
        safe_reference = self._sanitize_segment(attachment.client_reference)
        safe_filename = self._sanitize_segment(attachment.original_filename)
        return f"support/{ticket_code}/{safe_reference}/{safe_filename}"

    @staticmethod
    def _sanitize_segment(value: str) -> str:
        sanitized = "".join(
            character if character.isalnum() or character in {"-", "_", "."} else "-"
            for character in value.strip().lower()
        )
        return sanitized.strip("-._") or "artifact"


class SupportTicketNotFoundError(Exception):
    """Raised when a support ticket is not visible in the caller's account scope."""


class SupportTicketValidationError(Exception):
    """Raised when a support ticket request violates support-service rules."""


class SupportAccessRestrictedError(Exception):
    """Raised when the account lifecycle does not allow support access."""

    def __init__(self, status: str) -> None:
        super().__init__(f"Support access is restricted for status {status}.")
        self.status = status


class SupportService:
    def __init__(
        self,
        repository: SupportRepository,
        *,
        attachment_storage_planner: SupportAttachmentStoragePlanner | None = None,
    ) -> None:
        self._repository = repository
        self._attachment_storage_planner = (
            attachment_storage_planner or DefaultSupportAttachmentStoragePlanner()
        )

    def create_ticket(
        self,
        context: AuthenticatedSessionContext,
        payload: SupportTicketCreateRequest,
    ) -> SupportTicketCreateResponse:
        self._ensure_support_access(context)
        normalized_subject = payload.subject.strip()
        normalized_description = payload.description.strip()
        if not normalized_subject or not normalized_description:
            raise SupportTicketValidationError(
                "Support tickets require both a subject and description."
            )

        self._validate_request_vocabulary(payload)
        ticket_code = self._generate_ticket_code()
        planned_attachments = self._plan_attachments(payload.attachments, ticket_code=ticket_code)

        try:
            detail = self._repository.create_ticket(
                account_id=context.account_id,
                ticket_code=ticket_code,
                request_type=payload.request_type,
                related_product_code=payload.related_product_code,
                priority=payload.priority,
                subject=normalized_subject,
                description=normalized_description,
                status=SUPPORT_TICKET_STATUS.default or "open",
                estimated_response_sla_label=self._build_estimated_response_label(payload.priority),
                initial_message_author_type=SUPPORT_MESSAGE_AUTHOR_TYPE.default or "customer",
                initial_message_body=normalized_description,
                attachments=[
                    SupportAttachmentCreateInput(
                        uploaded_by_account_id=context.account_id,
                        storage_key=attachment.storage_key,
                        original_filename=attachment.original_filename,
                        content_type=attachment.content_type,
                        file_size_bytes=attachment.file_size_bytes,
                        scan_status=attachment.scan_status,
                    )
                    for attachment in planned_attachments
                ],
            )
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise

        return SupportTicketCreateResponse(
            message="Support ticket created.",
            ticket=self._build_ticket_summary(detail.ticket),
        )

    def list_tickets(
        self,
        context: AuthenticatedSessionContext,
        *,
        limit: int = DEFAULT_CURSOR_LIMIT,
        cursor: str | None = None,
    ) -> SupportTicketListResponse:
        self._ensure_support_access(context)
        normalized_limit = max(1, min(limit, MAX_CURSOR_LIMIT))
        created_before, ticket_id_before = self._decode_cursor(cursor)
        records = self._repository.list_tickets_for_account(
            context.account_id,
            limit=normalized_limit + 1,
            created_before=created_before,
            ticket_id_before=ticket_id_before,
        )
        page_records = records[:normalized_limit]
        next_cursor = None
        if len(records) > normalized_limit and page_records:
            last_record = page_records[-1]
            next_cursor = self._encode_cursor(last_record.created_at, last_record.ticket_id)

        return SupportTicketListResponse(
            items=[self._build_ticket_summary(record) for record in page_records],
            page=CursorPageInfo(limit=normalized_limit, cursor=cursor, next_cursor=next_cursor),
        )

    def get_ticket_detail(
        self,
        context: AuthenticatedSessionContext,
        ticket_id: UUID,
    ) -> SupportTicketDetailResponse:
        self._ensure_support_access(context)
        detail = self._repository.get_ticket_detail_for_account(context.account_id, ticket_id)
        if detail is None:
            raise SupportTicketNotFoundError(f"Support ticket {ticket_id} was not found.")

        return self._build_ticket_detail(detail)

    @staticmethod
    def _build_estimated_response_label(priority: str) -> str:
        return PRIORITY_SLA_LABELS.get(priority, DEFAULT_SLA_LABEL)

    @staticmethod
    def _ensure_support_access(context: AuthenticatedSessionContext) -> None:
        if context.status == "closed":
            raise SupportAccessRestrictedError(context.status)

    @staticmethod
    def _validate_request_vocabulary(payload: SupportTicketCreateRequest) -> None:
        if payload.request_type not in SUPPORT_REQUEST_TYPE.allowed_values:
            raise SupportTicketValidationError("Support request type is invalid.")
        if payload.priority not in SUPPORT_PRIORITY.allowed_values:
            raise SupportTicketValidationError("Support priority is invalid.")

    def _plan_attachments(
        self,
        attachments: list[SupportAttachmentMetadataReference],
        *,
        ticket_code: str,
    ) -> list[PlannedSupportAttachment]:
        seen_client_references: set[str] = set()
        seen_upload_tokens: set[str] = set()
        planned: list[PlannedSupportAttachment] = []
        for attachment in attachments:
            client_reference = attachment.client_reference.strip()
            upload_token = attachment.upload_token.strip()
            if client_reference in seen_client_references:
                raise SupportTicketValidationError(
                    "Support attachment client references must be unique."
                )
            if upload_token in seen_upload_tokens:
                raise SupportTicketValidationError("Support attachment upload tokens must be unique.")

            extension = self._extract_extension(attachment.original_filename)
            if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
                raise SupportTicketValidationError(
                    "Support attachment file type is not allowed."
                )

            seen_client_references.add(client_reference)
            seen_upload_tokens.add(upload_token)
            planned.append(
                PlannedSupportAttachment(
                    original_filename=attachment.original_filename,
                    content_type=attachment.content_type,
                    file_size_bytes=attachment.file_size_bytes,
                    scan_status=ATTACHMENT_SCAN_STATUS.default or "pending",
                    storage_key=self._attachment_storage_planner.build_storage_key(
                        ticket_code=ticket_code,
                        attachment=attachment,
                    ),
                )
            )

        return planned

    def _generate_ticket_code(self) -> str:
        for _ in range(10):
            candidate = f"{DEFAULT_TICKET_PREFIX}-{uuid4().hex[:8].upper()}"
            if not self._repository.ticket_code_exists(candidate):
                return candidate
        raise SupportTicketValidationError("Unable to allocate a unique support ticket code.")

    @staticmethod
    def _extract_extension(filename: str) -> str:
        filename = filename.strip().lower()
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", maxsplit=1)[-1]

    @staticmethod
    def _build_ticket_summary(record: SupportTicketRecord) -> SupportTicketSummary:
        return SupportTicketSummary(
            ticket_id=record.ticket_id,
            ticket_code=record.ticket_code,
            request_type=record.request_type,
            related_product_code=record.related_product_code,
            priority=record.priority,
            subject=record.subject,
            status=record.status,
            estimated_response_sla_label=record.estimated_response_sla_label,
            created_at=record.created_at,
            updated_at=record.updated_at,
            attachment_count=record.attachment_count,
        )

    def _build_ticket_detail(self, detail: SupportTicketDetailRecord) -> SupportTicketDetailResponse:
        return SupportTicketDetailResponse(
            ticket=self._build_ticket_summary(detail.ticket),
            description=detail.ticket.description,
            attachments=[self._build_attachment_summary(record) for record in detail.attachments],
        )

    @staticmethod
    def _build_attachment_summary(record: SupportAttachmentRecord) -> SupportAttachmentSummary:
        return SupportAttachmentSummary(
            attachment_id=record.attachment_id,
            original_filename=record.original_filename,
            content_type=record.content_type,
            file_size_bytes=record.file_size_bytes,
            scan_status=record.scan_status,
            uploaded_at=record.created_at,
        )

    @staticmethod
    def _encode_cursor(created_at: datetime, ticket_id: UUID) -> str:
        token = f"{created_at.astimezone(timezone.utc).isoformat()}|{ticket_id}"
        return urlsafe_b64encode(token.encode("utf-8")).decode("ascii")

    @staticmethod
    def _decode_cursor(cursor: str | None) -> tuple[datetime | None, UUID | None]:
        if cursor is None:
            return None, None

        try:
            decoded = urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
            created_at_raw, ticket_id_raw = decoded.split("|", maxsplit=1)
            created_at = datetime.fromisoformat(created_at_raw)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            return created_at, UUID(ticket_id_raw)
        except Exception as exc:  # pragma: no cover - defensive path
            raise SupportTicketValidationError("Support ticket cursor is invalid.") from exc


def build_support_service(db: Session) -> SupportService:
    return SupportService(SupportRepository(db))
