"""add training enrollment requires approval

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-03-16 11:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trainings",
        sa.Column(
            "enrollment_requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="报名是否需要审核",
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE trainings
            SET enrollment_requires_approval = TRUE
            WHERE enrollment_requires_approval IS NULL
            """
        )
    )
    op.alter_column("trainings", "enrollment_requires_approval", server_default=None)


def downgrade() -> None:
    op.drop_column("trainings", "enrollment_requires_approval")
