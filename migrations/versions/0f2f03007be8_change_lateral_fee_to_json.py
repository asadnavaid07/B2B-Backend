"""Change lateral_fee column to JSON structure

Revision ID: 0f2f03007be8
Revises: payment_models_001
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0f2f03007be8"
down_revision = "payment_models_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Alter `lateral_fee` column to JSONB storing tiered fees."""
    op.alter_column(
        "partnership_fees",
        "lateral_fee",
        existing_type=sa.Float(),
        type_=postgresql.JSONB(),
        postgresql_using="jsonb_build_object('1st', lateral_fee, '2nd', lateral_fee, '3rd', lateral_fee)",
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert `lateral_fee` column back to float (using '1st' tier)."""
    op.alter_column(
        "partnership_fees",
        "lateral_fee",
        existing_type=postgresql.JSONB(),
        type_=sa.Float(),
        postgresql_using="COALESCE((lateral_fee->>'1st')::double precision, 0)",
        existing_nullable=False,
    )

