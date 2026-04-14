"""pdb-055 support ticket attachment metadata table

Revision ID: 20260413_2055
Revises: 20260413_2105
Create Date: 2026-04-13 20:55:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2055"
down_revision: str | None = "20260413_2105"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_ticket_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("scan_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_support_ticket_attachments_ticket_id",
        "support_ticket_attachments",
        ["ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_ticket_attachments_uploaded_by_account_id",
        "support_ticket_attachments",
        ["uploaded_by_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_ticket_attachments_scan_status",
        "support_ticket_attachments",
        ["scan_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_ticket_attachments_scan_status", table_name="support_ticket_attachments")
    op.drop_index(
        "ix_support_ticket_attachments_uploaded_by_account_id",
        table_name="support_ticket_attachments",
    )
    op.drop_index("ix_support_ticket_attachments_ticket_id", table_name="support_ticket_attachments")
    op.drop_table("support_ticket_attachments")
