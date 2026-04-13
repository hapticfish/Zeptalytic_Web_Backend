"""pdb-025 account security and auth audit tables

Revision ID: 20260413_1910
Revises: 20260413_1835
Create Date: 2026-04-13 19:10:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260413_1910"
down_revision: str | None = "20260413_1835"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_security_settings",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("two_factor_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("two_factor_method", sa.String(length=32), nullable=True),
        sa.Column(
            "recovery_methods_available_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("recovery_codes_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )

    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_hash"),
    )
    op.create_index("ix_mfa_recovery_codes_account_id", "mfa_recovery_codes", ["account_id"], unique=False)

    op.create_table(
        "auth_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_events_account_id", "auth_events", ["account_id"], unique=False)
    op.create_index("ix_auth_events_event_type", "auth_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_auth_events_event_type", table_name="auth_events")
    op.drop_index("ix_auth_events_account_id", table_name="auth_events")
    op.drop_table("auth_events")

    op.drop_index("ix_mfa_recovery_codes_account_id", table_name="mfa_recovery_codes")
    op.drop_table("mfa_recovery_codes")

    op.drop_table("account_security_settings")
