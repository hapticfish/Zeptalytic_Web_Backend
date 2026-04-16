"""rdb-010 add reward account and reward event foundation tables

Revision ID: 20260415_2355
Revises: 20260415_2345
Create Date: 2026-04-15 23:55:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260415_2355"
down_revision: str | None = "20260415_2345"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reward_accounts",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column(
            "current_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "current_tier",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'BRONZE'"),
        ),
        sa.Column(
            "current_tier_progress_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "next_milestone_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column("last_recomputed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("account_id"),
    )

    op.create_table(
        "reward_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("points_delta", sa.Integer(), nullable=False),
        sa.Column("objective_definition_id", sa.Uuid(), nullable=True),
        sa.Column("reward_definition_id", sa.Uuid(), nullable=True),
        sa.Column("badge_definition_id", sa.Uuid(), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column(
            "is_reversal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("reversed_event_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
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
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reversed_event_id"], ["reward_events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reward_events_account_id", "reward_events", ["account_id"], unique=False)
    op.create_index("ix_reward_events_created_at", "reward_events", ["created_at"], unique=False)
    op.create_index(
        "ix_reward_events_reversed_event_id",
        "reward_events",
        ["reversed_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reward_events_reversed_event_id", table_name="reward_events")
    op.drop_index("ix_reward_events_created_at", table_name="reward_events")
    op.drop_index("ix_reward_events_account_id", table_name="reward_events")
    op.drop_table("reward_events")
    op.drop_table("reward_accounts")
