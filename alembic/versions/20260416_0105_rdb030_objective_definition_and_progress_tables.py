"""rdb-030 add objective definition and progress tables

Revision ID: 20260416_0105
Revises: 20260416_0010
Create Date: 2026-04-16 01:05:00-05:00
"""

from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "20260416_0105"
down_revision: str | None = "20260416_0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _milestone_objective_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sort_order, milestone_points in enumerate(range(100, 5001, 100), start=1):
        tier_index = min((milestone_points - 1) // 1000, 4)
        tier_code = ("BRONZE", "SILVER", "GOLD", "PLATINUM", "PLUS")[tier_index]
        rows.append(
            {
                "id": uuid4(),
                "objective_code": f"milestone_{milestone_points:04d}",
                "title": f"Reach {milestone_points} Points",
                "description": f"Reach {milestone_points} total reward points.",
                "scope_type": "global",
                "product_code": None,
                "objective_type": "milestone",
                "is_repeatable": False,
                "repeat_group_key": None,
                "required_count": 1,
                "tier_gate": None,
                "subscription_gate_product_code": None,
                "subscription_gate_plan_code": None,
                "is_milestone_objective": True,
                "sort_group": "milestones",
                "sort_order": sort_order,
                "active": True,
                "metadata": {
                    "milestone_points": milestone_points,
                    "tier_code": tier_code,
                    "is_tier_boundary": milestone_points % 1000 == 0,
                },
            }
        )
    return rows


def upgrade() -> None:
    op.create_table(
        "objective_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("objective_code", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("objective_type", sa.String(length=64), nullable=False),
        sa.Column(
            "is_repeatable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("repeat_group_key", sa.String(length=128), nullable=True),
        sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tier_gate", sa.String(length=32), nullable=True),
        sa.Column("subscription_gate_product_code", sa.String(length=64), nullable=True),
        sa.Column("subscription_gate_plan_code", sa.String(length=64), nullable=True),
        sa.Column(
            "is_milestone_objective",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("sort_group", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_objective_definitions_scope_type",
        "objective_definitions",
        ["scope_type"],
        unique=False,
    )
    op.create_index(
        "ix_objective_definitions_sort_group_sort_order",
        "objective_definitions",
        ["sort_group", "sort_order"],
        unique=False,
    )
    op.create_index(
        "uq_objective_definitions_objective_code",
        "objective_definitions",
        ["objective_code"],
        unique=True,
    )

    objective_definitions = sa.table(
        "objective_definitions",
        sa.column("id", sa.Uuid()),
        sa.column("objective_code", sa.String(length=128)),
        sa.column("title", sa.String(length=255)),
        sa.column("description", sa.String(length=1024)),
        sa.column("scope_type", sa.String(length=32)),
        sa.column("product_code", sa.String(length=64)),
        sa.column("objective_type", sa.String(length=64)),
        sa.column("is_repeatable", sa.Boolean()),
        sa.column("repeat_group_key", sa.String(length=128)),
        sa.column("required_count", sa.Integer()),
        sa.column("tier_gate", sa.String(length=32)),
        sa.column("subscription_gate_product_code", sa.String(length=64)),
        sa.column("subscription_gate_plan_code", sa.String(length=64)),
        sa.column("is_milestone_objective", sa.Boolean()),
        sa.column("sort_group", sa.String(length=64)),
        sa.column("sort_order", sa.Integer()),
        sa.column("active", sa.Boolean()),
        sa.column("metadata", sa.JSON()),
    )
    milestone_rows = _milestone_objective_rows()
    op.bulk_insert(objective_definitions, milestone_rows)

    op.create_table(
        "account_objective_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("objective_definition_id", sa.Uuid(), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_progress_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repeat_iteration", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
        sa.ForeignKeyConstraint(
            ["objective_definition_id"],
            ["objective_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_account_objective_progress_account_id",
        "account_objective_progress",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_account_objective_progress_objective_definition_id",
        "account_objective_progress",
        ["objective_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_account_objective_progress_status",
        "account_objective_progress",
        ["status"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_reward_milestones_linked_objective",
        "reward_milestones",
        "objective_definitions",
        ["linked_objective_definition_id"],
        ["id"],
        ondelete="SET NULL",
    )

    milestone_mapping = sa.table(
        "reward_milestones",
        sa.column("id", sa.Uuid()),
        sa.column("milestone_points", sa.Integer()),
        sa.column("linked_objective_definition_id", sa.Uuid()),
    )
    bind = op.get_bind()
    objective_rows_by_points = {
        row["metadata"]["milestone_points"]: row["id"] for row in milestone_rows
    }
    for milestone_id, milestone_points in bind.execute(
        sa.select(milestone_mapping.c.id, milestone_mapping.c.milestone_points)
    ):
        bind.execute(
            milestone_mapping.update()
            .where(milestone_mapping.c.id == milestone_id)
            .values(
                linked_objective_definition_id=objective_rows_by_points[milestone_points]
            )
        )

    op.alter_column("objective_definitions", "is_repeatable", server_default=None)
    op.alter_column("objective_definitions", "required_count", server_default=None)
    op.alter_column("objective_definitions", "is_milestone_objective", server_default=None)
    op.alter_column("objective_definitions", "active", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "fk_reward_milestones_linked_objective",
        "reward_milestones",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_account_objective_progress_status",
        table_name="account_objective_progress",
    )
    op.drop_index(
        "ix_account_objective_progress_objective_definition_id",
        table_name="account_objective_progress",
    )
    op.drop_index(
        "ix_account_objective_progress_account_id",
        table_name="account_objective_progress",
    )
    op.drop_table("account_objective_progress")
    op.drop_index(
        "uq_objective_definitions_objective_code",
        table_name="objective_definitions",
    )
    op.drop_index(
        "ix_objective_definitions_sort_group_sort_order",
        table_name="objective_definitions",
    )
    op.drop_index(
        "ix_objective_definitions_scope_type",
        table_name="objective_definitions",
    )
    op.drop_table("objective_definitions")
