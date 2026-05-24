"""email-010 add email send attempts table

Revision ID: 20260524_1710
Revises: 20260416_0245
Create Date: 2026-05-24 17:10:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260524_1710"
down_revision: str | None = "20260416_0245"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_send_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("from_email", sa.String(length=320), nullable=False),
        sa.Column("from_name", sa.String(length=255), nullable=True),
        sa.Column("reply_to_email", sa.String(length=320), nullable=True),
        sa.Column("template_key", sa.String(length=64), nullable=False),
        sa.Column(
            "provider",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'brevo'"),
        ),
        sa.Column("provider_template_id", sa.Integer(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
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
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_send_attempts_account_id", "email_send_attempts", ["account_id"], unique=False)
    op.create_index("ix_email_send_attempts_to_email", "email_send_attempts", ["to_email"], unique=False)
    op.create_index(
        "ix_email_send_attempts_template_key",
        "email_send_attempts",
        ["template_key"],
        unique=False,
    )
    op.create_index("ix_email_send_attempts_status", "email_send_attempts", ["status"], unique=False)
    op.create_index(
        "ix_email_send_attempts_provider_message_id",
        "email_send_attempts",
        ["provider_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_email_send_attempts_created_at",
        "email_send_attempts",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_send_attempts_created_at", table_name="email_send_attempts")
    op.drop_index("ix_email_send_attempts_provider_message_id", table_name="email_send_attempts")
    op.drop_index("ix_email_send_attempts_status", table_name="email_send_attempts")
    op.drop_index("ix_email_send_attempts_template_key", table_name="email_send_attempts")
    op.drop_index("ix_email_send_attempts_to_email", table_name="email_send_attempts")
    op.drop_index("ix_email_send_attempts_account_id", table_name="email_send_attempts")
    op.drop_table("email_send_attempts")
