"""next change

Revision ID: f8d91eea1c32
Revises: 02ad23ac23b5
Create Date: 2025-08-15 20:03:45.957653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8d91eea1c32'
down_revision: Union[str, Sequence[str], None] = '02ad23ac23b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
