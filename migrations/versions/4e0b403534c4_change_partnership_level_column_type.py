"""Convert users.partnership_level column to JSONB arrays

Revision ID: 4e0b403534c4
Revises: 3d5482ab7a64
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "4e0b403534c4"
down_revision = "3d5482ab7a64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "partnership_level",
        existing_type=sa.String(),
        type_=postgresql.JSONB(),
        postgresql_using="""
        CASE
            WHEN partnership_level IS NULL OR btrim(partnership_level::text) = '' THEN '[]'::jsonb
            ELSE partnership_level::jsonb
        END
        """,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "partnership_level",
        existing_type=postgresql.JSONB(),
        type_=sa.String(),
        postgresql_using="partnership_level::text",
    )
