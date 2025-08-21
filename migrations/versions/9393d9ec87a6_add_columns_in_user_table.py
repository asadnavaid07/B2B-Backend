"""add columns in user table

Revision ID: 9393d9ec87a6
Revises: 6a5712c50df2
Create Date: 2025-08-20 17:05:36.240237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9393d9ec87a6'
down_revision: Union[str, Sequence[str], None] = '6a5712c50df2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely for existing rows."""
    # 1. Add columns as nullable first
    op.add_column(
        'users',
        sa.Column(
            'is_registered',
            sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='registrationstatus'),
            nullable=True
        )
    )
    op.add_column(
        'users',
        sa.Column('registration_step', sa.Integer(), nullable=True)
    )

    # 2. Set default values for existing rows
    op.execute("UPDATE users SET is_registered = 'PENDING', registration_step = 0")

    # 3. Alter to enforce NOT NULL
    op.alter_column('users', 'is_registered', nullable=False)
    op.alter_column('users', 'registration_step', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'registration_step')
    op.drop_column('users', 'is_registered')
    # also drop enum if you want to clean schema
    op.execute("DROP TYPE IF EXISTS registrationstatus")
