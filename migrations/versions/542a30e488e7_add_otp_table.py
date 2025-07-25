"""Add OTP table

Revision ID: 542a30e488e7
Revises: 663495cf9c27
Create Date: 2025-07-25 00:48:03.692075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '542a30e488e7'
down_revision: Union[str, Sequence[str], None] = '663495cf9c27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
