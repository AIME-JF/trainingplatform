"""add_admission_exam_scope_fields

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-03-14 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("admission_exams"):
        return

    column_names = {column["name"] for column in inspector.get_columns("admission_exams")}
    if "scope_type" not in column_names:
        op.add_column(
            "admission_exams",
            sa.Column(
                "scope_type",
                sa.String(length=30),
                nullable=True,
                server_default=sa.text("'all'"),
                comment="适用范围类型: all/user/department/role",
            ),
        )
    if "scope_target_ids" not in column_names:
        op.add_column(
            "admission_exams",
            sa.Column(
                "scope_target_ids",
                sa.JSON(),
                nullable=True,
                comment="适用范围目标ID列表",
            ),
        )

    bind.execute(sa.text(
        """
        UPDATE admission_exams
        SET
            scope_type = COALESCE(NULLIF(scope_type, ''), 'all'),
            scope = CASE
                WHEN scope IS NULL OR scope = '' THEN '全体学员'
                ELSE scope
            END
        """
    ))

    op.alter_column(
        "admission_exams",
        "scope_type",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default=sa.text("'all'"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("admission_exams"):
        return

    column_names = {column["name"] for column in inspector.get_columns("admission_exams")}
    if "scope_target_ids" in column_names:
        op.drop_column("admission_exams", "scope_target_ids")
    if "scope_type" in column_names:
        op.drop_column("admission_exams", "scope_type")
