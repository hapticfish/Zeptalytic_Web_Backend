from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.support_ticket_attachments import SupportTicketAttachment
from app.db.models.support_ticket_messages import SupportTicketMessage
from app.db.models.support_tickets import SupportTicket


@dataclass(slots=True)
class SupportAttachmentCreateInput:
    uploaded_by_account_id: UUID
    storage_key: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    scan_status: str


@dataclass(slots=True)
class SupportAttachmentRecord:
    attachment_id: UUID
    ticket_id: UUID
    uploaded_by_account_id: UUID
    storage_key: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    scan_status: str
    created_at: datetime


@dataclass(slots=True)
class SupportTicketRecord:
    ticket_id: UUID
    account_id: UUID
    ticket_code: str
    request_type: str
    related_product_code: str | None
    priority: str
    subject: str
    description: str
    status: str
    estimated_response_sla_label: str | None
    created_at: datetime
    updated_at: datetime
    attachment_count: int


@dataclass(slots=True)
class SupportTicketDetailRecord:
    ticket: SupportTicketRecord
    attachments: list[SupportAttachmentRecord]


class SupportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def ticket_code_exists(self, ticket_code: str) -> bool:
        statement = select(SupportTicket.id).where(SupportTicket.ticket_code == ticket_code).limit(1)
        return self._db.scalar(statement) is not None

    def create_ticket(
        self,
        *,
        account_id: UUID,
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
        ticket = SupportTicket(
            account_id=account_id,
            ticket_code=ticket_code,
            request_type=request_type,
            related_product_code=related_product_code,
            priority=priority,
            subject=subject,
            description=description,
            status=status,
            estimated_response_sla_label=estimated_response_sla_label,
        )
        self._db.add(ticket)
        self._db.flush()

        self._db.add(
            SupportTicketMessage(
                ticket_id=ticket.id,
                account_id=account_id,
                author_type=initial_message_author_type,
                message_body=initial_message_body,
                is_internal_note=False,
            )
        )

        for attachment in attachments:
            self._db.add(
                SupportTicketAttachment(
                    ticket_id=ticket.id,
                    uploaded_by_account_id=attachment.uploaded_by_account_id,
                    storage_key=attachment.storage_key,
                    original_filename=attachment.original_filename,
                    content_type=attachment.content_type,
                    file_size_bytes=attachment.file_size_bytes,
                    scan_status=attachment.scan_status,
                )
            )

        self._db.flush()
        detail = self.get_ticket_detail_for_account(account_id, ticket.id)
        if detail is None:
            raise AssertionError("Expected persisted support ticket detail after create.")
        return detail

    def list_tickets_for_account(
        self,
        account_id: UUID,
        *,
        limit: int,
        created_before: datetime | None = None,
        ticket_id_before: UUID | None = None,
    ) -> list[SupportTicketRecord]:
        statement = (
            select(SupportTicket)
            .where(SupportTicket.account_id == account_id)
            .options(selectinload(SupportTicket.attachments))
            .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
            .limit(limit)
        )
        if created_before is not None and ticket_id_before is not None:
            statement = statement.where(
                or_(
                    SupportTicket.created_at < created_before,
                    and_(
                        SupportTicket.created_at == created_before,
                        SupportTicket.id < ticket_id_before,
                    ),
                )
            )

        tickets = self._db.scalars(statement).all()
        return [self._to_ticket_record(ticket) for ticket in tickets]

    def get_ticket_detail_for_account(
        self,
        account_id: UUID,
        ticket_id: UUID,
    ) -> SupportTicketDetailRecord | None:
        statement = (
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id, SupportTicket.account_id == account_id)
            .options(selectinload(SupportTicket.attachments))
        )
        ticket = self._db.scalar(statement)
        if ticket is None:
            return None

        return SupportTicketDetailRecord(
            ticket=self._to_ticket_record(ticket),
            attachments=[self._to_attachment_record(item) for item in ticket.attachments],
        )

    @staticmethod
    def _to_ticket_record(ticket: SupportTicket) -> SupportTicketRecord:
        return SupportTicketRecord(
            ticket_id=ticket.id,
            account_id=ticket.account_id,
            ticket_code=ticket.ticket_code,
            request_type=ticket.request_type,
            related_product_code=ticket.related_product_code,
            priority=ticket.priority,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status,
            estimated_response_sla_label=ticket.estimated_response_sla_label,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            attachment_count=len(ticket.attachments),
        )

    @staticmethod
    def _to_attachment_record(attachment: SupportTicketAttachment) -> SupportAttachmentRecord:
        return SupportAttachmentRecord(
            attachment_id=attachment.id,
            ticket_id=attachment.ticket_id,
            uploaded_by_account_id=attachment.uploaded_by_account_id,
            storage_key=attachment.storage_key,
            original_filename=attachment.original_filename,
            content_type=attachment.content_type,
            file_size_bytes=attachment.file_size_bytes,
            scan_status=attachment.scan_status,
            created_at=attachment.created_at,
        )
