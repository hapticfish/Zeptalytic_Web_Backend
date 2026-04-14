"""pdb-040 addresses table

Revision ID: 20260413_2040
Revises: 20260413_1830
Create Date: 2026-04-13 20:40:00-05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2040"
down_revision: str | None = "20260413_1830"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("address_type", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city_or_locality", sa.String(length=128), nullable=False),
        sa.Column("state_or_region", sa.String(length=128), nullable=True),
        sa.Column("postal_code", sa.String(length=32), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("country_name", sa.String(length=128), nullable=True),
        sa.Column("formatted_address", sa.String(length=1024), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_account_id", "addresses", ["account_id"], unique=False)
    op.create_index(
        "ix_addresses_account_id_address_type",
        "addresses",
        ["account_id", "address_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_addresses_account_id_address_type", table_name="addresses")
    op.drop_index("ix_addresses_account_id", table_name="addresses")
    op.drop_table("addresses")
