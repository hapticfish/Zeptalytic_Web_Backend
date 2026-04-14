"""pdb-070 subscription and entitlement summary tables

Revision ID: 20260413_2115
Revises: 20260413_2108
Create Date: 2026-04-13 21:15:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2115"
down_revision: str | None = "20260413_2108"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscription_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("plan_code", sa.String(length=64), nullable=False),
        sa.Column("billing_interval", sa.String(length=32), nullable=False),
        sa.Column("normalized_status", sa.String(length=32), nullable=False),
        sa.Column("provider_status_raw", sa.String(length=64), nullable=False),
        sa.Column("current_period_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_billing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_subscription_summaries_account_id",
        "subscription_summaries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_subscription_summaries_product_code",
        "subscription_summaries",
        ["product_code"],
        unique=False,
    )

    op.create_table(
        "entitlement_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("plan_code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entitlement_summaries_account_id",
        "entitlement_summaries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_entitlement_summaries_product_code",
        "entitlement_summaries",
        ["product_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_entitlement_summaries_product_code", table_name="entitlement_summaries")
    op.drop_index("ix_entitlement_summaries_account_id", table_name="entitlement_summaries")
    op.drop_table("entitlement_summaries")
    op.drop_index("ix_subscription_summaries_product_code", table_name="subscription_summaries")
    op.drop_index("ix_subscription_summaries_account_id", table_name="subscription_summaries")
    op.drop_table("subscription_summaries")
