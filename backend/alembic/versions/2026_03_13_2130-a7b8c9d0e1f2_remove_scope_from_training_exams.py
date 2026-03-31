"""remove_scope_from_training_exams

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-13 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("exams"):
        exam_columns = {column["name"] for column in inspector.get_columns("exams")}
        if "scope" in exam_columns:
            op.drop_column("exams", "scope")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("exams"):
        exam_columns = {column["name"] for column in inspector.get_columns("exams")}
        if "scope" not in exam_columns:
            op.add_column(
                "exams",
                sa.Column("scope", sa.String(length=200), nullable=True, comment="适用范围"),
            )
