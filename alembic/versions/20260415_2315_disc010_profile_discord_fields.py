"""disc-010 align active Discord linkage on profiles

Revision ID: 20260415_2315
Revises: 20260413_2128
Create Date: 2026-04-15 23:15:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260415_2315"
down_revision: str | None = "20260413_2128"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("discord_user_id", sa.String(length=255), nullable=True))
    op.add_column(
        "profiles",
        sa.Column(
            "discord_integration_status",
            sa.String(length=32),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
    )

    op.execute(
        """
        WITH latest_discord_connection AS (
            SELECT DISTINCT ON (account_id)
                account_id,
                provider_user_id,
                provider_username,
                status
            FROM oauth_connections
            WHERE provider = 'discord'
            ORDER BY account_id, connected_at DESC, id DESC
        )
        UPDATE profiles
        SET
            discord_user_id = latest_discord_connection.provider_user_id,
            discord_username = COALESCE(profiles.discord_username, latest_discord_connection.provider_username),
            discord_integration_status = latest_discord_connection.status
        FROM latest_discord_connection
        WHERE profiles.account_id = latest_discord_connection.account_id
        """
    )

    op.alter_column("profiles", "discord_integration_status", server_default=None)


def downgrade() -> None:
    op.drop_column("profiles", "discord_integration_status")
    op.drop_column("profiles", "discord_user_id")
