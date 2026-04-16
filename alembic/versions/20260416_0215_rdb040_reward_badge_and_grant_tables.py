"""rdb-040 add reward, badge, grant, and achievement tables

Revision ID: 20260416_0215
Revises: 20260416_0105
Create Date: 2026-04-16 02:15:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260416_0215"
down_revision: str | None = "20260416_0105"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reward_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reward_code", sa.String(length=128), nullable=False),
        sa.Column("reward_type", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column(
            "is_repeatable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_revocable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("grant_mode", sa.String(length=64), nullable=False),
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
        "ix_reward_definitions_reward_type",
        "reward_definitions",
        ["reward_type"],
        unique=False,
    )
    op.create_index(
        "uq_reward_definitions_reward_code",
        "reward_definitions",
        ["reward_code"],
        unique=True,
    )

    op.create_table(
        "badge_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("badge_code", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column("icon_ref", sa.String(length=255), nullable=True),
        sa.Column(
            "is_revocable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        "ix_badge_definitions_display_name",
        "badge_definitions",
        ["display_name"],
        unique=False,
    )
    op.create_index(
        "uq_badge_definitions_badge_code",
        "badge_definitions",
        ["badge_code"],
        unique=True,
    )

    op.create_table(
        "objective_reward_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("objective_definition_id", sa.Uuid(), nullable=False),
        sa.Column("reward_definition_id", sa.Uuid(), nullable=False),
        sa.Column("grant_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["objective_definition_id"],
            ["objective_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reward_definition_id"],
            ["reward_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_objective_reward_links_objective_definition_id",
        "objective_reward_links",
        ["objective_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_objective_reward_links_reward_definition_id",
        "objective_reward_links",
        ["reward_definition_id"],
        unique=False,
    )
    op.create_index(
        "uq_objective_reward_links_objective_reward",
        "objective_reward_links",
        ["objective_definition_id", "reward_definition_id"],
        unique=True,
    )

    op.create_table(
        "reward_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("reward_definition_id", sa.Uuid(), nullable=False),
        sa.Column("source_objective_definition_id", sa.Uuid(), nullable=True),
        sa.Column("source_reward_event_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reward_definition_id"],
            ["reward_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_objective_definition_id"],
            ["objective_definitions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_reward_event_id"],
            ["reward_events.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reward_grants_account_id", "reward_grants", ["account_id"], unique=False)
    op.create_index(
        "ix_reward_grants_reward_definition_id",
        "reward_grants",
        ["reward_definition_id"],
        unique=False,
    )
    op.create_index("ix_reward_grants_status", "reward_grants", ["status"], unique=False)

    op.create_table(
        "account_badges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("badge_definition_id", sa.Uuid(), nullable=False),
        sa.Column(
            "earned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=255), nullable=True),
        sa.Column("source_objective_definition_id", sa.Uuid(), nullable=True),
        sa.Column("source_reward_event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["badge_definition_id"],
            ["badge_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_objective_definition_id"],
            ["objective_definitions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_reward_event_id"],
            ["reward_events.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_account_badges_account_id",
        "account_badges",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_account_badges_badge_definition_id",
        "account_badges",
        ["badge_definition_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_reward_events_objective_definition",
        "reward_events",
        "objective_definitions",
        ["objective_definition_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_reward_events_reward_definition",
        "reward_events",
        "reward_definitions",
        ["reward_definition_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_reward_events_badge_definition",
        "reward_events",
        "badge_definitions",
        ["badge_definition_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("reward_definitions", "is_repeatable", server_default=None)
    op.alter_column("reward_definitions", "is_revocable", server_default=None)
    op.alter_column("badge_definitions", "is_revocable", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "fk_reward_events_badge_definition",
        "reward_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_reward_events_reward_definition",
        "reward_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_reward_events_objective_definition",
        "reward_events",
        type_="foreignkey",
    )
    op.drop_index("ix_account_badges_badge_definition_id", table_name="account_badges")
    op.drop_index("ix_account_badges_account_id", table_name="account_badges")
    op.drop_table("account_badges")
    op.drop_index("ix_reward_grants_status", table_name="reward_grants")
    op.drop_index("ix_reward_grants_reward_definition_id", table_name="reward_grants")
    op.drop_index("ix_reward_grants_account_id", table_name="reward_grants")
    op.drop_table("reward_grants")
    op.drop_index(
        "uq_objective_reward_links_objective_reward",
        table_name="objective_reward_links",
    )
    op.drop_index(
        "ix_objective_reward_links_reward_definition_id",
        table_name="objective_reward_links",
    )
    op.drop_index(
        "ix_objective_reward_links_objective_definition_id",
        table_name="objective_reward_links",
    )
    op.drop_table("objective_reward_links")
    op.drop_index("uq_badge_definitions_badge_code", table_name="badge_definitions")
    op.drop_index("ix_badge_definitions_display_name", table_name="badge_definitions")
    op.drop_table("badge_definitions")
    op.drop_index("uq_reward_definitions_reward_code", table_name="reward_definitions")
    op.drop_index("ix_reward_definitions_reward_type", table_name="reward_definitions")
    op.drop_table("reward_definitions")
