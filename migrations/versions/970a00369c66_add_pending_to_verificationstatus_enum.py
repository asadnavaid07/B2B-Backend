"""Add Pending to verificationstatus enum

Revision ID: 970a00369c66
Revises: 76d564fd9afe
Create Date: 2025-08-14 13:35:18.539866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '970a00369c66'
down_revision: Union[str, Sequence[str], None] = '76d564fd9afe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
