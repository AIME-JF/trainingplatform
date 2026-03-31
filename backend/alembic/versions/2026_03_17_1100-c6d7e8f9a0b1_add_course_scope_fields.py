"""add_course_scope_fields

Revision ID: c6d7e8f9a0b1
Revises: 2bad6e1b18de
Create Date: 2026-03-17 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "c6d7e8f9a0b1"
down_revision: Union[str, None] = "2bad6e1b18de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("courses"):
        return

    column_names = {column["name"] for column in inspector.get_columns("courses")}
    if "scope" not in column_names:
        op.add_column(
            "courses",
            sa.Column(
                "scope",
                sa.String(length=200),
                nullable=True,
                comment="可见范围摘要",
            ),
        )
    if "scope_type" not in column_names:
        op.add_column(
            "courses",
            sa.Column(
                "scope_type",
                sa.String(length=30),
                nullable=True,
                server_default=sa.text("'all'"),
                comment="可见范围类型: all/user/department/role",
            ),
        )
    if "scope_target_ids" not in column_names:
        op.add_column(
            "courses",
            sa.Column(
                "scope_target_ids",
                sa.JSON(),
                nullable=True,
                comment="可见范围目标ID列表",
            ),
        )

    bind.execute(sa.text(
        """
        UPDATE courses
        SET
            scope_type = COALESCE(NULLIF(scope_type, ''), 'all'),
            scope = CASE
                WHEN scope IS NULL OR scope = '' THEN '全体用户'
                ELSE scope
            END
        """
    ))

    op.alter_column(
        "courses",
        "scope_type",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default=sa.text("'all'"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("courses"):
        return

    column_names = {column["name"] for column in inspector.get_columns("courses")}
    if "scope_target_ids" in column_names:
        op.drop_column("courses", "scope_target_ids")
    if "scope_type" in column_names:
        op.drop_column("courses", "scope_type")
    if "scope" in column_names:
        op.drop_column("courses", "scope")
