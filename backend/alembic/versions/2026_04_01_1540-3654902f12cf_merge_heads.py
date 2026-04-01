"""merge_heads

Revision ID: 3654902f12cf
Revises: a3d174a9a2c7, b4c5d6e7f8a9
Create Date: 2026-04-01 15:40:06.680418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3654902f12cf'
down_revision: Union[str, None] = ('a3d174a9a2c7', 'b4c5d6e7f8a9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
