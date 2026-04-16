from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_status", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # TODO(john): Lock the allowed account-status vocabulary in the auth spec/decision record.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    # TODO(john): Lock the launch role vocabulary in the auth spec/decision record.
    role: Mapped[str] = mapped_column(String(32), nullable=False)
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
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    profile: Mapped["Profile | None"] = relationship(
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )
    profile_preferences: Mapped["ProfilePreference | None"] = relationship(
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )
    communication_preferences: Mapped["CommunicationPreference | None"] = relationship(
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )
    discord_connection_history: Mapped[list["DiscordConnectionHistory"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    oauth_connections: Mapped[list["OAuthConnection"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    support_tickets: Mapped[list["SupportTicket"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    support_ticket_messages: Mapped[list["SupportTicketMessage"]] = relationship(
        back_populates="author_account",
    )
    uploaded_support_ticket_attachments: Mapped[list["SupportTicketAttachment"]] = relationship(
        back_populates="uploaded_by_account",
    )
    subscription_summaries: Mapped[list["SubscriptionSummary"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    entitlement_summaries: Mapped[list["EntitlementSummary"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    product_access_states: Mapped[list["ProductAccessState"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    payment_summaries: Mapped[list["PaymentSummary"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    payment_method_summaries: Mapped[list["PaymentMethodSummary"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    reward_account: Mapped["RewardAccount | None"] = relationship(
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reward_events: Mapped[list["RewardEvent"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        foreign_keys="RewardEvent.account_id",
    )
