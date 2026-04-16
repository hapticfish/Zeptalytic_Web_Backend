"""rdb-050 add reward notification queue table

Revision ID: 20260416_0245
Revises: 20260416_0215
Create Date: 2026-04-16 02:45:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260416_0245"
down_revision: str | None = "20260416_0215"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reward_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("objective_definition_id", sa.Uuid(), nullable=True),
        sa.Column("reward_grant_id", sa.Uuid(), nullable=True),
        sa.Column("badge_definition_id", sa.Uuid(), nullable=True),
        sa.Column("reward_event_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["objective_definition_id"],
            ["objective_definitions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reward_grant_id"],
            ["reward_grants.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["badge_definition_id"],
            ["badge_definitions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reward_event_id"],
            ["reward_events.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reward_notifications_account_id",
        "reward_notifications",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_reward_notifications_status",
        "reward_notifications",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_reward_notifications_sequence_order",
        "reward_notifications",
        ["sequence_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reward_notifications_sequence_order", table_name="reward_notifications")
    op.drop_index("ix_reward_notifications_status", table_name="reward_notifications")
    op.drop_index("ix_reward_notifications_account_id", table_name="reward_notifications")
    op.drop_table("reward_notifications")
