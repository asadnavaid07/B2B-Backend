"""Add Pending to verificationstatus enum

Revision ID: 76d564fd9afe
Revises: 17e1fd84e3da
Create Date: 2025-08-14 13:25:16.713176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76d564fd9afe'
down_revision: Union[str, Sequence[str], None] = '17e1fd84e3da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
