"""fix video keyframe task resource fk on delete

Revision ID: 4b847d29017c
Revises: 1dfb8ab36d03
Create Date: 2026-04-09 16:02:04.125706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b847d29017c'
down_revision: Union[str, None] = '1dfb8ab36d03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_has_on_delete(table: str, constraint_name: str, expected_action: str) -> bool:
    """检查外键约束是否已有指定的 ON DELETE 动作"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT confdeltype FROM pg_constraint "
        "WHERE conname = :name AND conrelid = :table::regclass"
    ), {"name": constraint_name, "table": table})
    row = result.scalar()
    # confdeltype: a=NO ACTION, r=RESTRICT, c=CASCADE, n=SET NULL, d=SET DEFAULT
    action_map = {"NO ACTION": "a", "RESTRICT": "r", "CASCADE": "c", "SET NULL": "n", "SET DEFAULT": "d"}
    return row == action_map.get(expected_action.upper())


def upgrade() -> None:
    constraint_name = "video_keyframe_tasks_resource_id_fkey"
    if not _fk_has_on_delete("video_keyframe_tasks", constraint_name, "SET NULL"):
        op.drop_constraint(constraint_name, "video_keyframe_tasks", type_="foreignkey")
        op.create_foreign_key(
            constraint_name, "video_keyframe_tasks",
            "resources", ["resource_id"], ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    constraint_name = "video_keyframe_tasks_resource_id_fkey"
    if _fk_has_on_delete("video_keyframe_tasks", constraint_name, "SET NULL"):
        op.drop_constraint(constraint_name, "video_keyframe_tasks", type_="foreignkey")
        op.create_foreign_key(
            constraint_name, "video_keyframe_tasks",
            "resources", ["resource_id"], ["id"],
        )
