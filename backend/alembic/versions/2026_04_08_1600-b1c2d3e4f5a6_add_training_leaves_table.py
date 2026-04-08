"""add training_leaves table

Revision ID: b1c2d3e4f5a6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-08 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "training_leaves" in inspector.get_table_names():
        return

    op.create_table(
        "training_leaves",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("training_id", sa.Integer(), sa.ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_key", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="leave_active"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_leave_training_user_session", "training_leaves", ["training_id", "user_id", "session_key"])
    op.create_index("ix_leave_training_session", "training_leaves", ["training_id", "session_key"])


def downgrade() -> None:
    op.drop_index("ix_leave_training_session", table_name="training_leaves")
    op.drop_constraint("uq_leave_training_user_session", "training_leaves", type_="unique")
    op.drop_table("training_leaves")
