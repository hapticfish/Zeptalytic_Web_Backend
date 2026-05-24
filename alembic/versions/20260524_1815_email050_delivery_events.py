"""email-050 add email delivery events table

Revision ID: 20260524_1815
Revises: 20260524_1710
Create Date: 2026-05-24 18:15:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260524_1815"
down_revision: str | None = "20260524_1710"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_delivery_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "provider",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'brevo'"),
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
        sa.Column(
            "raw_payload",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_delivery_events_provider_message_id",
        "email_delivery_events",
        ["provider_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_email_delivery_events_provider_event_id",
        "email_delivery_events",
        ["provider_event_id"],
        unique=False,
    )
    op.create_index("ix_email_delivery_events_email", "email_delivery_events", ["email"], unique=False)
    op.create_index(
        "ix_email_delivery_events_event_type",
        "email_delivery_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_email_delivery_events_template_id",
        "email_delivery_events",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        "ix_email_delivery_events_event_timestamp",
        "email_delivery_events",
        ["event_timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_email_delivery_events_created_at",
        "email_delivery_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ux_email_delivery_events_dedupe_key",
        "email_delivery_events",
        ["dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_email_delivery_events_dedupe_key", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_created_at", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_event_timestamp", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_template_id", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_event_type", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_email", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_provider_event_id", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_provider_message_id", table_name="email_delivery_events")
    op.drop_table("email_delivery_events")
