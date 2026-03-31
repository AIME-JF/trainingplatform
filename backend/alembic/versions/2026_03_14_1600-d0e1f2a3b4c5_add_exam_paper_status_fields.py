"""add_exam_paper_status_fields

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-03-14 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("exam_papers"):
        return

    column_names = {column["name"] for column in inspector.get_columns("exam_papers")}
    if "status" not in column_names:
        op.add_column(
            "exam_papers",
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=True,
                server_default=sa.text("'draft'"),
                comment="试卷状态: draft/published/archived",
            ),
        )
    if "published_at" not in column_names:
        op.add_column(
            "exam_papers",
            sa.Column(
                "published_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="发布时间",
            ),
        )

    bind.execute(sa.text(
        """
        UPDATE exam_papers
        SET
            status = CASE
                WHEN id IN (
                    SELECT paper_id FROM exams WHERE paper_id IS NOT NULL
                    UNION
                    SELECT paper_id FROM admission_exams WHERE paper_id IS NOT NULL
                ) THEN 'published'
                ELSE COALESCE(NULLIF(status, ''), 'draft')
            END,
            published_at = CASE
                WHEN id IN (
                    SELECT paper_id FROM exams WHERE paper_id IS NOT NULL
                    UNION
                    SELECT paper_id FROM admission_exams WHERE paper_id IS NOT NULL
                ) THEN COALESCE(published_at, created_at, CURRENT_TIMESTAMP)
                ELSE published_at
            END
        """
    ))

    op.alter_column(
        "exam_papers",
        "status",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'draft'"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("exam_papers"):
        return

    column_names = {column["name"] for column in inspector.get_columns("exam_papers")}
    if "published_at" in column_names:
        op.drop_column("exam_papers", "published_at")
    if "status" in column_names:
        op.drop_column("exam_papers", "status")
