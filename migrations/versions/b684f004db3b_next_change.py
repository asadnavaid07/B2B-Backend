"""next change

Revision ID: b684f004db3b
Revises: d2cf83a3a4cd
Create Date: 2025-08-15 19:50:37.544920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b684f004db3b'
down_revision: Union[str, Sequence[str], None] = 'd2cf83a3a4cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
