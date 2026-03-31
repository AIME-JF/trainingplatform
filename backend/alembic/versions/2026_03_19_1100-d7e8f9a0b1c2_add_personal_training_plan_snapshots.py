"""add personal training plan snapshots

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-03-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "c6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personal_training_plan_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ai_task_id", sa.Integer(), nullable=False, comment="来源 AI 任务 ID"),
        sa.Column("training_id", sa.Integer(), nullable=False, comment="培训班 ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="学员 ID"),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1", comment="同一培训同一学员的版本号"),
        sa.Column("task_name", sa.String(length=200), nullable=False, comment="任务名称快照"),
        sa.Column("request_payload", sa.JSON(), nullable=False, comment="任务请求快照"),
        sa.Column("portrait_payload", sa.JSON(), nullable=False, comment="画像快照"),
        sa.Column("plan_payload", sa.JSON(), nullable=False, comment="方案快照"),
        sa.Column("summary", sa.Text(), nullable=True, comment="方案摘要"),
        sa.Column("created_by", sa.Integer(), nullable=False, comment="任务创建人"),
        sa.Column("confirmed_by", sa.Integer(), nullable=False, comment="确认人"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="确认时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.ForeignKeyConstraint(["ai_task_id"], ["ai_tasks.id"]),
        sa.ForeignKeyConstraint(["training_id"], ["trainings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("training_id", "user_id", "version_no", name="uq_personal_training_snapshot_version"),
    )
    op.create_index(op.f("ix_personal_training_plan_snapshots_ai_task_id"), "personal_training_plan_snapshots", ["ai_task_id"], unique=False)
    op.create_index(op.f("ix_personal_training_plan_snapshots_id"), "personal_training_plan_snapshots", ["id"], unique=False)
    op.create_index(op.f("ix_personal_training_plan_snapshots_training_id"), "personal_training_plan_snapshots", ["training_id"], unique=False)
    op.create_index(op.f("ix_personal_training_plan_snapshots_user_id"), "personal_training_plan_snapshots", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_personal_training_plan_snapshots_user_id"), table_name="personal_training_plan_snapshots")
    op.drop_index(op.f("ix_personal_training_plan_snapshots_training_id"), table_name="personal_training_plan_snapshots")
    op.drop_index(op.f("ix_personal_training_plan_snapshots_id"), table_name="personal_training_plan_snapshots")
    op.drop_index(op.f("ix_personal_training_plan_snapshots_ai_task_id"), table_name="personal_training_plan_snapshots")
    op.drop_table("personal_training_plan_snapshots")
