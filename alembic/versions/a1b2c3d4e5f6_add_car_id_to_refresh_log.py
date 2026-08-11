"""add car_id to refresh_log

Revision ID: a1b2c3d4e5f6
Revises: 23ffb3a62cee
Create Date: 2026-08-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '23ffb3a62cee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE refresh_log
        ADD COLUMN IF NOT EXISTS car_id INTEGER REFERENCES cars(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.drop_column('refresh_log', 'car_id')
