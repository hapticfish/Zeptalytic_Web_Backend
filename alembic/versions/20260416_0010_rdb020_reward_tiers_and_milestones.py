"""rdb-020 add reward tier and milestone definition tables

Revision ID: 20260416_0010
Revises: 20260415_2355
Create Date: 2026-04-16 00:10:00-05:00
"""

from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "20260416_0010"
down_revision: str | None = "20260415_2355"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


TIER_ROWS = (
    {
        "id": uuid4(),
        "tier_code": "BRONZE",
        "display_name": "Bronze",
        "sort_order": 1,
        "tier_start_points": 0,
        "tier_end_points": 999,
    },
    {
        "id": uuid4(),
        "tier_code": "SILVER",
        "display_name": "Silver",
        "sort_order": 2,
        "tier_start_points": 1000,
        "tier_end_points": 1999,
    },
    {
        "id": uuid4(),
        "tier_code": "GOLD",
        "display_name": "Gold",
        "sort_order": 3,
        "tier_start_points": 2000,
        "tier_end_points": 2999,
    },
    {
        "id": uuid4(),
        "tier_code": "PLATINUM",
        "display_name": "Platinum",
        "sort_order": 4,
        "tier_start_points": 3000,
        "tier_end_points": 3999,
    },
    {
        "id": uuid4(),
        "tier_code": "PLUS",
        "display_name": "Plus",
        "sort_order": 5,
        "tier_start_points": 4000,
        "tier_end_points": 4999,
    },
)


def _milestone_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sort_order, milestone_points in enumerate(range(100, 5001, 100), start=1):
        tier_index = min((milestone_points - 1) // 1000, len(TIER_ROWS) - 1)
        rows.append(
            {
                "id": uuid4(),
                "milestone_points": milestone_points,
                "tier_code": TIER_ROWS[tier_index]["tier_code"],
                "is_tier_boundary": milestone_points % 1000 == 0,
                "linked_objective_definition_id": None,
                "sort_order": sort_order,
            }
        )
    return rows


def upgrade() -> None:
    op.create_table(
        "reward_tier_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tier_code", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("tier_start_points", sa.Integer(), nullable=False),
        sa.Column("tier_end_points", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reward_tier_definitions_sort_order",
        "reward_tier_definitions",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "uq_reward_tier_definitions_tier_code",
        "reward_tier_definitions",
        ["tier_code"],
        unique=True,
    )

    op.create_table(
        "reward_milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("milestone_points", sa.Integer(), nullable=False),
        sa.Column("tier_code", sa.String(length=32), nullable=False),
        sa.Column(
            "is_tier_boundary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("linked_objective_definition_id", sa.Uuid(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reward_milestones_sort_order",
        "reward_milestones",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "uq_reward_milestones_milestone_points",
        "reward_milestones",
        ["milestone_points"],
        unique=True,
    )

    reward_tier_definitions = sa.table(
        "reward_tier_definitions",
        sa.column("id", sa.Uuid()),
        sa.column("tier_code", sa.String(length=32)),
        sa.column("display_name", sa.String(length=32)),
        sa.column("sort_order", sa.Integer()),
        sa.column("tier_start_points", sa.Integer()),
        sa.column("tier_end_points", sa.Integer()),
    )
    reward_milestones = sa.table(
        "reward_milestones",
        sa.column("id", sa.Uuid()),
        sa.column("milestone_points", sa.Integer()),
        sa.column("tier_code", sa.String(length=32)),
        sa.column("is_tier_boundary", sa.Boolean()),
        sa.column("linked_objective_definition_id", sa.Uuid()),
        sa.column("sort_order", sa.Integer()),
    )
    op.bulk_insert(reward_tier_definitions, list(TIER_ROWS))
    op.bulk_insert(reward_milestones, _milestone_rows())

    op.alter_column("reward_milestones", "is_tier_boundary", server_default=None)


def downgrade() -> None:
    op.drop_index("uq_reward_milestones_milestone_points", table_name="reward_milestones")
    op.drop_index("ix_reward_milestones_sort_order", table_name="reward_milestones")
    op.drop_table("reward_milestones")
    op.drop_index("uq_reward_tier_definitions_tier_code", table_name="reward_tier_definitions")
    op.drop_index("ix_reward_tier_definitions_sort_order", table_name="reward_tier_definitions")
    op.drop_table("reward_tier_definitions")
