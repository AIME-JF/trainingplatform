"""add multi_select config format

Revision ID: b3c4d5e6f7a8
Revises: 9c2e1f4a6b7d
Create Date: 2026-04-02 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "9c2e1f4a6b7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE configformat ADD VALUE IF NOT EXISTS 'MULTI_SELECT'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    pass
