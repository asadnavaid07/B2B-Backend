"""merge multiple heads

Revision ID: 198072bd54df
Revises: c2baec940431, f07dbabbba1e, fd69bf138c63
Create Date: 2025-08-28 00:07:08.442668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '198072bd54df'
down_revision: Union[str, Sequence[str], None] = ('c2baec940431', 'f07dbabbba1e', 'fd69bf138c63')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
