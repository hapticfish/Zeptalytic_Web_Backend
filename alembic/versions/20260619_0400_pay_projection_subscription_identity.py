"""pay projection subscription commercial identity

Revision ID: 20260619_0400
Revises: 20260524_1815
Create Date: 2026-06-19 04:00:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260619_0400"
down_revision: str | None = "20260524_1815"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "subscription_summaries",
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "subscription_summaries",
        sa.Column("provider_customer_reference", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "subscription_summaries",
        sa.Column("bundle_code", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "subscription_summaries",
        sa.Column(
            "commercial_subject_type",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'product'"),
        ),
    )
    op.add_column(
        "subscription_summaries",
        sa.Column("commercial_subject_code", sa.String(length=128), nullable=True),
    )

    op.execute(
        """
        UPDATE subscription_summaries
        SET commercial_subject_code = plan_code
        WHERE commercial_subject_code IS NULL
        """
    )

    op.create_index(
        "ix_subscription_summaries_provider_subscription_id",
        "subscription_summaries",
        ["provider_subscription_id"],
        unique=False,
    )
    op.create_index(
        "ix_subscription_summaries_bundle_code",
        "subscription_summaries",
        ["bundle_code"],
        unique=False,
    )
    op.create_index(
        "ix_subscription_summaries_commercial_subject",
        "subscription_summaries",
        ["account_id", "commercial_subject_type", "commercial_subject_code"],
        unique=False,
    )
    op.create_index(
        "uq_subscription_summaries_account_provider_subscription_id",
        "subscription_summaries",
        ["account_id", "provider_subscription_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_subscription_summaries_account_provider_subscription_id",
        table_name="subscription_summaries",
    )
    op.drop_index(
        "ix_subscription_summaries_commercial_subject",
        table_name="subscription_summaries",
    )
    op.drop_index(
        "ix_subscription_summaries_bundle_code",
        table_name="subscription_summaries",
    )
    op.drop_index(
        "ix_subscription_summaries_provider_subscription_id",
        table_name="subscription_summaries",
    )

    op.drop_column("subscription_summaries", "commercial_subject_code")
    op.drop_column("subscription_summaries", "commercial_subject_type")
    op.drop_column("subscription_summaries", "bundle_code")
    op.drop_column("subscription_summaries", "provider_customer_reference")
    op.drop_column("subscription_summaries", "provider_subscription_id")
