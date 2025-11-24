"""Add partnership_level column to registration_agreements

Revision ID: 7b33c6b7d8f5
Revises: 4e0b403534c4
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "7b33c6b7d8f5"
down_revision = "4e0b403534c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    partnership_enum = postgresql.ENUM(
        "DROP_SHIPPING",
        "CONSIGNMENT",
        "IMPORT_EXPORT",
        "WHOLESALE",
        "EXHIBITION",
        "AUCTION",
        "WHITE_LABEL",
        "BRICK_MORTRAR",
        "DESIGN_COLLABORATION",
        "STORYTELLING",
        "WAREHOUSE",
        "PACKAGING",
        "LOGISTICS",
        "MUSEUM_INSTITUTIONAL",
        "NGO_GOVERNMENT",
        "TECHNOLOGY_PARTNERSHIP",
        name="partnershiplevel",
        create_type=False,
    )

    op.add_column(
        "registration_agreements",
        sa.Column(
            "partnership_level",
            partnership_enum,
            nullable=False,
            server_default="DROP_SHIPPING",
        ),
    )
    # Remove default now that column is populated
    op.alter_column(
        "registration_agreements",
        "partnership_level",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("registration_agreements", "partnership_level")

