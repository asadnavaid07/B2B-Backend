"""Add REGISTRATION to paymenttype enum

Revision ID: a1b2c3d4e5f6
Revises: 4e0b403534c4
Create Date: 2025-01-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '99dee79b4d2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'registration' to the paymenttype enum
    op.execute("ALTER TYPE paymenttype ADD VALUE IF NOT EXISTS 'registration'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum and updating all references
    # For now, we'll leave it as a no-op
    pass

