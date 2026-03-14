"""add_ai_task_table

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-03-14 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("ai_tasks"):
        return

    op.create_table(
        "ai_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_name", sa.String(length=200), nullable=False, comment="任务名称"),
        sa.Column("task_type", sa.String(length=50), nullable=False, comment="任务类型"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="任务状态",
        ),
        sa.Column("request_payload", sa.JSON(), nullable=False, comment="任务请求参数快照"),
        sa.Column("result_payload", sa.JSON(), nullable=True, comment="任务结果快照"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="任务错误信息"),
        sa.Column("confirmed_question_ids", sa.JSON(), nullable=True, comment="确认后的题目 ID 列表"),
        sa.Column(
            "confirmed_paper_id",
            sa.Integer(),
            sa.ForeignKey("exam_papers.id"),
            nullable=True,
            comment="确认后的试卷 ID",
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            comment="创建人 ID",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_tasks_task_type", "ai_tasks", ["task_type"], unique=False)
    op.create_index("ix_ai_tasks_status", "ai_tasks", ["status"], unique=False)
    op.create_index("ix_ai_tasks_created_by", "ai_tasks", ["created_by"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("ai_tasks"):
        return

    index_names = {index["name"] for index in inspector.get_indexes("ai_tasks")}
    if "ix_ai_tasks_created_by" in index_names:
        op.drop_index("ix_ai_tasks_created_by", table_name="ai_tasks")
    if "ix_ai_tasks_status" in index_names:
        op.drop_index("ix_ai_tasks_status", table_name="ai_tasks")
    if "ix_ai_tasks_task_type" in index_names:
        op.drop_index("ix_ai_tasks_task_type", table_name="ai_tasks")
    op.drop_table("ai_tasks")
