"""added appointment model

Revision ID: 02ae3760981e
Revises: 6989644b0cba
Create Date: 2025-08-14 16:55:48.539286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02ae3760981e'
down_revision: Union[str, Sequence[str], None] = '6989644b0cba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
