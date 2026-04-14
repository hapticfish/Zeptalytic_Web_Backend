from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._json import JSON_VARIANT
from app.db.models.accounts import Account


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # TODO(john): Lock the announcement scope vocabulary in the content/dashboard spec.
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(8000), nullable=False)
    # TODO(john): Lock the announcement severity vocabulary in the content/dashboard spec.
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class ServiceStatus(Base):
    __tablename__ = "service_statuses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the service-status vocabulary in the dashboard/status spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SubscriptionSummary(Base):
    __tablename__ = "subscription_summaries"
    __table_args__ = (
        Index("ix_subscription_summaries_account_id", "account_id"),
        Index("ix_subscription_summaries_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the billing-interval vocabulary in the Pay integration contract/spec.
    billing_interval: Mapped[str] = mapped_column(String(32), nullable=False)
    # TODO(john): Lock the normalized subscription-status vocabulary in the Pay integration contract/spec.
    normalized_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_status_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    current_period_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="subscription_summaries")


class EntitlementSummary(Base):
    __tablename__ = "entitlement_summaries"
    __table_args__ = (
        Index("ix_entitlement_summaries_account_id", "account_id"),
        Index("ix_entitlement_summaries_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the normalized entitlement-status vocabulary in the Pay integration contract/spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entitlement_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON_VARIANT,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="entitlement_summaries")


class ProductAccessState(Base):
    __tablename__ = "product_access_states"
    __table_args__ = (
        Index("ix_product_access_states_account_id", "account_id"),
        Index("ix_product_access_states_product_code", "product_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the launcher access-state vocabulary in the dashboard/launcher spec.
    access_state: Mapped[str] = mapped_column(String(32), nullable=False)
    launch_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    disabled_reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    external_account_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account] = relationship(back_populates="product_access_states")


class PaymentSummary(Base):
    __tablename__ = "payment_summaries"
    __table_args__ = (
        Index("ix_payment_summaries_account_id", "account_id"),
        Index("ix_payment_summaries_product_code", "product_code"),
        Index("ix_payment_summaries_payment_rail", "payment_rail"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # TODO(john): Lock the payment-rail vocabulary in the Pay integration contract/spec.
    payment_rail: Mapped[str] = mapped_column(String(32), nullable=False)
    # TODO(john): Lock the normalized payment-status vocabulary in the Pay integration contract/spec.
    normalized_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_status_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account] = relationship(back_populates="payment_summaries")


class PaymentMethodSummary(Base):
    __tablename__ = "payment_method_summaries"
    __table_args__ = (
        Index("ix_payment_method_summaries_account_id", "account_id"),
        Index(
            "uq_payment_method_summaries_provider_method",
            "provider",
            "provider_payment_method_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_payment_method_id: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(32), nullable=False)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    exp_month: Mapped[int] = mapped_column(Integer, nullable=False)
    exp_year: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    # TODO(john): Lock the payment-method summary status vocabulary in the billing spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[Account] = relationship(back_populates="payment_method_summaries")


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
