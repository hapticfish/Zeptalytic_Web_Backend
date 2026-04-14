from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account
from app.db.models.support_tickets import SupportTicket


class SupportTicketAttachment(Base):
    __tablename__ = "support_ticket_attachments"
    __table_args__ = (
        Index("ix_support_ticket_attachments_ticket_id", "ticket_id"),
        Index("ix_support_ticket_attachments_uploaded_by_account_id", "uploaded_by_account_id"),
        Index("ix_support_ticket_attachments_scan_status", "scan_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by_account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    # TODO(john): Lock the attachment scan-status vocabulary in the support spec.
    scan_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ticket: Mapped[SupportTicket] = relationship(back_populates="attachments")
    uploaded_by_account: Mapped[Account] = relationship(back_populates="uploaded_support_ticket_attachments")
