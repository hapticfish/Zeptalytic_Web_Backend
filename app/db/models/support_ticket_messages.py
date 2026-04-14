from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.accounts import Account
from app.db.models.support_tickets import SupportTicket


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"
    __table_args__ = (
        Index("ix_support_ticket_messages_ticket_id", "ticket_id"),
        Index("ix_support_ticket_messages_account_id", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    # TODO(john): Lock the support message author-type vocabulary in the support spec.
    author_type: Mapped[str] = mapped_column(String(32), nullable=False)
    message_body: Mapped[str] = mapped_column(String(8000), nullable=False)
    is_internal_note: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ticket: Mapped[SupportTicket] = relationship(back_populates="messages")
    author_account: Mapped[Account | None] = relationship(back_populates="support_ticket_messages")
