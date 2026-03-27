"""add ai resource generation snapshots

Revision ID: 0a9b8c7d6e5f
Revises: f9a0b1c2d3e4
Create Date: 2026-03-26 15:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "0a9b8c7d6e5f"
down_revision: Union[str, None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, "ai_resource_generation_snapshots"):
        return

    op.create_table(
        "ai_resource_generation_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ai_task_id", sa.Integer(), nullable=False, comment="来源 AI 任务 ID"),
        sa.Column("resource_id", sa.Integer(), nullable=False, comment="确认后的资源 ID"),
        sa.Column("media_file_id", sa.Integer(), nullable=False, comment="生成文件 ID"),
        sa.Column("template_code", sa.String(length=100), nullable=False, comment="内容模板编码"),
        sa.Column("task_name", sa.String(length=200), nullable=False, comment="任务名称快照"),
        sa.Column("resource_title", sa.String(length=200), nullable=False, comment="资源标题快照"),
        sa.Column("request_payload", sa.JSON(), nullable=False, comment="任务请求快照"),
        sa.Column("parsed_request", sa.JSON(), nullable=True, comment="解析结果快照"),
        sa.Column("template_payload", sa.JSON(), nullable=True, comment="模板快照"),
        sa.Column("page_plan", sa.JSON(), nullable=True, comment="页面方案快照"),
        sa.Column("html_content", sa.Text(), nullable=False, comment="生成的 HTML 内容"),
        sa.Column("created_by", sa.Integer(), nullable=False, comment="任务创建人"),
        sa.Column("confirmed_by", sa.Integer(), nullable=False, comment="确认人"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["ai_task_id"], ["ai_tasks.id"]),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"]),
        sa.ForeignKeyConstraint(["media_file_id"], ["media_files.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.UniqueConstraint("ai_task_id", name="uq_ai_resource_generation_snapshot_task"),
    )
    op.create_index(
        "ix_ai_resource_generation_snapshots_ai_task_id",
        "ai_resource_generation_snapshots",
        ["ai_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_resource_generation_snapshots_resource_id",
        "ai_resource_generation_snapshots",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_resource_generation_snapshots_media_file_id",
        "ai_resource_generation_snapshots",
        ["media_file_id"],
        unique=False,
    )


def downgrade() -> None:
    pass
