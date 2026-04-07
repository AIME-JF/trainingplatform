"""add training_plans table

Revision ID: 5b9ab54afbd4
Revises: c8d9e0f1a2b3
Create Date: 2026-04-07 13:52:47.577341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b9ab54afbd4'
down_revision: Union[str, None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
