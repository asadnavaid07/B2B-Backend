"""next change

Revision ID: d2cf83a3a4cd
Revises: 02ae3760981e
Create Date: 2025-08-15 19:43:48.205400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2cf83a3a4cd'
down_revision: Union[str, Sequence[str], None] = '02ae3760981e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
