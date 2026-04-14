"""pdb-035 profile/settings/integration tables

Revision ID: 20260413_1830
Revises: 20260413_1918
Create Date: 2026-04-13 18:30:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260413_1830"
down_revision: str | None = "20260413_1918"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profile_preferences",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("preferred_language", sa.String(length=16), nullable=True),
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
        sa.PrimaryKeyConstraint("account_id"),
    )

    op.create_table(
        "communication_preferences",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("marketing_emails_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("product_updates_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("announcement_emails_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("account_id"),
    )

    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_username", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "connected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oauth_connections_account_id", "oauth_connections", ["account_id"], unique=False)
    op.create_index(
        "uq_oauth_connections_provider_user",
        "oauth_connections",
        ["provider", "provider_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_oauth_connections_provider_user", table_name="oauth_connections")
    op.drop_index("ix_oauth_connections_account_id", table_name="oauth_connections")
    op.drop_table("oauth_connections")

    op.drop_table("communication_preferences")

    op.drop_table("profile_preferences")
