"""Normalize partnership_level column to JSON arrays

Revision ID: 3d5482ab7a64
Revises: 0f2f03007be8
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = "3d5482ab7a64"
down_revision = "0f2f03007be8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    results = conn.execute(sa.text("SELECT id, partnership_level FROM users")).fetchall()

    for row in results:
        user_id = row.id
        raw_value = row.partnership_level

        normalized = normalize_partnership_level(raw_value)
        conn.execute(
            sa.text("UPDATE users SET partnership_level = :value WHERE id = :id"),
            {"id": user_id, "value": json.dumps(normalized)},
        )


def downgrade() -> None:
    # No safe automatic downgrade; retain current data shape
    pass


def normalize_partnership_level(value):
    """Return a list representation for any stored partnership_level variant."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, str):
                return [parsed]
        except json.JSONDecodeError:
            return [stripped]
    if isinstance(value, dict):
        # Unexpected structure, wrap entire value
        return [value]
    return [value]

