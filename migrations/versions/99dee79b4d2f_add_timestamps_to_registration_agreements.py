"""Add timestamps to registration_agreements

Revision ID: 99dee79b4d2f
Revises: 7b33c6b7d8f5
Create Date: 2025-11-24
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "99dee79b4d2f"
down_revision = "7b33c6b7d8f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'registration_agreements' 
                  AND column_name = 'created_at'
            ) THEN
                ALTER TABLE registration_agreements
                ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now();
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'registration_agreements' 
                  AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE registration_agreements
                ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE registration_agreements 
        DROP COLUMN IF EXISTS updated_at;
        ALTER TABLE registration_agreements 
        DROP COLUMN IF EXISTS created_at;
        """
    )

