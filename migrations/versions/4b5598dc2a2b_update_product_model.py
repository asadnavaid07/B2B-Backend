"""update product model

Revision ID: 4b5598dc2a2b
Revises: 970a00369c66
Create Date: 2025-08-14 15:39:47.479427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b5598dc2a2b'
down_revision: Union[str, Sequence[str], None] = '970a00369c66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
