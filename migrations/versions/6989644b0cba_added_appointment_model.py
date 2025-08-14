"""added appointment model

Revision ID: 6989644b0cba
Revises: 4b5598dc2a2b
Create Date: 2025-08-14 16:40:34.729336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6989644b0cba'
down_revision: Union[str, Sequence[str], None] = '4b5598dc2a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
