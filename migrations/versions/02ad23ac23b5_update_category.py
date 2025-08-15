"""update category

Revision ID: 02ad23ac23b5
Revises: b684f004db3b
Create Date: 2025-08-15 19:55:13.727859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02ad23ac23b5'
down_revision: Union[str, Sequence[str], None] = 'b684f004db3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
