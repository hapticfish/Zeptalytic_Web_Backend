"""pdb-050 support tickets and messages tables

Revision ID: 20260413_2105
Revises: 20260413_2040
Create Date: 2026-04-13 21:05:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2105"
down_revision: str | None = "20260413_2040"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_code", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("request_type", sa.String(length=32), nullable=False),
        sa.Column("related_product_code", sa.String(length=64), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("estimated_response_sla_label", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_code"),
    )
    op.create_index("ix_support_tickets_account_id", "support_tickets", ["account_id"], unique=False)
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"], unique=False)

    op.create_table(
        "support_ticket_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("author_type", sa.String(length=32), nullable=False),
        sa.Column("message_body", sa.String(length=8000), nullable=False),
        sa.Column("is_internal_note", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_support_ticket_messages_ticket_id",
        "support_ticket_messages",
        ["ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_ticket_messages_account_id",
        "support_ticket_messages",
        ["account_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_ticket_messages_account_id", table_name="support_ticket_messages")
    op.drop_index("ix_support_ticket_messages_ticket_id", table_name="support_ticket_messages")
    op.drop_table("support_ticket_messages")
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_index("ix_support_tickets_account_id", table_name="support_tickets")
    op.drop_table("support_tickets")
