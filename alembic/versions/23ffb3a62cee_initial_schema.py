"""initial schema

Revision ID: 23ffb3a62cee
Revises:
Create Date: 2026-08-11 14:20:30.690791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23ffb3a62cee'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables that didn't yet exist — safe to run on existing databases
    from app.database import Base, engine
    from app.models import Car, PriceHistory, RefreshLog  # noqa: F401
    Base.metadata.create_all(bind=engine, checkfirst=True)


def downgrade() -> None:
    pass
