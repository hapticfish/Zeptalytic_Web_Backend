from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        Index("ix_support_tickets_account_id", "account_id"),
        Index("ix_support_tickets_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    ticket_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    # TODO(john): Lock the support request-type vocabulary in the support spec.
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    related_product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # TODO(john): Lock the support priority vocabulary in the support spec.
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    # TODO(john): Lock the support ticket status vocabulary in the support spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    estimated_response_sla_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account] = relationship(back_populates="support_tickets")
    messages: Mapped[list["SupportTicketMessage"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["SupportTicketAttachment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
