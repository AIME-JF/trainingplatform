"""add_exam_course_bindings

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-02 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns(table_name)
    return any(column.get("name") == column_name for column in columns)


def upgrade() -> None:
    if not _column_exists("exams", "course_ids"):
        op.add_column("exams", sa.Column("course_ids", sa.JSON(), nullable=True, comment="显式绑定课程ID列表"))

    if not _column_exists("admission_exams", "course_ids"):
        op.add_column("admission_exams", sa.Column("course_ids", sa.JSON(), nullable=True, comment="显式绑定课程ID列表"))


def downgrade() -> None:
    if _column_exists("admission_exams", "course_ids"):
        op.drop_column("admission_exams", "course_ids")

    if _column_exists("exams", "course_ids"):
        op.drop_column("exams", "course_ids")
