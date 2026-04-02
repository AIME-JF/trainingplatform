"""add notice reminder type and read tracking

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-02 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("notices")}

    if "target_user_id" not in existing_columns:
        op.add_column("notices", sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, comment="目标用户ID(提醒类通知)"))
        op.create_index("ix_notices_target_user_id", "notices", ["target_user_id"])

    if "reminder_type" not in existing_columns:
        op.add_column("notices", sa.Column("reminder_type", sa.String(50), nullable=True, comment="提醒子类型"))

    if "notice_reads" not in inspector.get_table_names():
        op.create_table(
            "notice_reads",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("notice_id", sa.Integer(), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("notice_id", "user_id", name="uq_notice_read_user"),
        )


def downgrade() -> None:
    op.drop_table("notice_reads")
    op.drop_index("ix_notices_target_user_id", table_name="notices")
    op.drop_column("notices", "reminder_type")
    op.drop_column("notices", "target_user_id")
