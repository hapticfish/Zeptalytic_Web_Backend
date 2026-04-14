"""pdb-075 product access and payment summary tables

Revision ID: 20260413_2128
Revises: 20260413_2115
Create Date: 2026-04-13 21:28:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2128"
down_revision: str | None = "20260413_2115"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_access_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("access_state", sa.String(length=32), nullable=False),
        sa.Column("launch_url", sa.String(length=2048), nullable=True),
        sa.Column("disabled_reason", sa.String(length=1024), nullable=True),
        sa.Column("external_account_reference", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_access_states_account_id",
        "product_access_states",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_access_states_product_code",
        "product_access_states",
        ["product_code"],
        unique=False,
    )

    op.create_table(
        "payment_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("payment_rail", sa.String(length=32), nullable=False),
        sa.Column("normalized_status", sa.String(length=32), nullable=False),
        sa.Column("provider_status_raw", sa.String(length=64), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_payment_reference", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_summaries_account_id",
        "payment_summaries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_summaries_product_code",
        "payment_summaries",
        ["product_code"],
        unique=False,
    )
    op.create_index(
        "ix_payment_summaries_payment_rail",
        "payment_summaries",
        ["payment_rail"],
        unique=False,
    )

    op.create_table(
        "payment_method_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=False),
        sa.Column("provider_payment_method_id", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=32), nullable=False),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column("exp_month", sa.Integer(), nullable=False),
        sa.Column("exp_year", sa.Integer(), nullable=False),
        sa.Column("billing_name", sa.String(length=255), nullable=True),
        sa.Column("billing_country", sa.String(length=2), nullable=True),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_method_summaries_account_id",
        "payment_method_summaries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "uq_payment_method_summaries_provider_method",
        "payment_method_summaries",
        ["provider", "provider_payment_method_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_payment_method_summaries_provider_method",
        table_name="payment_method_summaries",
    )
    op.drop_index(
        "ix_payment_method_summaries_account_id",
        table_name="payment_method_summaries",
    )
    op.drop_table("payment_method_summaries")
    op.drop_index("ix_payment_summaries_payment_rail", table_name="payment_summaries")
    op.drop_index("ix_payment_summaries_product_code", table_name="payment_summaries")
    op.drop_index("ix_payment_summaries_account_id", table_name="payment_summaries")
    op.drop_table("payment_summaries")
    op.drop_index("ix_product_access_states_product_code", table_name="product_access_states")
    op.drop_index("ix_product_access_states_account_id", table_name="product_access_states")
    op.drop_table("product_access_states")
