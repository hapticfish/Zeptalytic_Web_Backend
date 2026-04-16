"""disc-020 add preserved Discord connection history table

Revision ID: 20260415_2345
Revises: 20260415_2315
Create Date: 2026-04-15 23:45:00-05:00
"""

from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "20260415_2345"
down_revision: str | None = "20260415_2315"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "discord_connection_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("discord_user_id", sa.String(length=255), nullable=False),
        sa.Column("discord_username", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_discord_connection_history_account_id",
        "discord_connection_history",
        ["account_id"],
        unique=False,
    )

    connection = op.get_bind()
    existing_history_rows = connection.execute(
        sa.text(
            """
            SELECT
                account_id,
                provider_user_id,
                provider_username,
                status,
                connected_at,
                COALESCE(disconnected_at, connected_at) AS updated_at
            FROM oauth_connections
            WHERE provider = 'discord'
            """
        )
    )
    discord_history_rows = existing_history_rows.mappings().all()

    if discord_history_rows:
        discord_history_table = sa.table(
            "discord_connection_history",
            sa.column("id", sa.Uuid()),
            sa.column("account_id", sa.Uuid()),
            sa.column("discord_user_id", sa.String(length=255)),
            sa.column("discord_username", sa.String(length=64)),
            sa.column("status", sa.String(length=32)),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(
            discord_history_table,
            [
                {
                    "id": uuid4(),
                    "account_id": row["account_id"],
                    "discord_user_id": row["provider_user_id"],
                    "discord_username": row["provider_username"],
                    "status": row["status"],
                    "created_at": row["connected_at"],
                    "updated_at": row["updated_at"],
                }
                for row in discord_history_rows
            ],
        )

    op.alter_column("discord_connection_history", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_discord_connection_history_account_id", table_name="discord_connection_history")
    op.drop_table("discord_connection_history")
