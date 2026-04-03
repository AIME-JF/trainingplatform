"""restrict course permissions for instructor

Revision ID: e7f8a9b0c1d2
Revises: f4c029187adf
Create Date: 2026-04-03 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "f4c029187adf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    required_tables = {"roles", "permissions", "role_permissions"}
    if not required_tables.issubset(set(inspector.get_table_names())):
        return

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String(length=50)),
    )
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String(length=100)),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer()),
        sa.column("permission_id", sa.Integer()),
    )

    instructor_role_id = bind.execute(
        sa.select(roles_table.c.id).where(roles_table.c.code == "instructor")
    ).scalar()
    if instructor_role_id is None:
        return

    permission_rows = bind.execute(
        sa.select(permissions_table.c.id).where(
            permissions_table.c.code.in_(["CREATE_COURSE", "UPDATE_COURSE"])
        )
    ).fetchall()
    permission_ids = [permission_id for (permission_id,) in permission_rows]
    if not permission_ids:
        return

    bind.execute(
        sa.delete(role_permissions_table).where(
            role_permissions_table.c.role_id == instructor_role_id,
            role_permissions_table.c.permission_id.in_(permission_ids),
        )
    )


def downgrade() -> None:
    # 权限回收属于兼容性收口，降级时不自动恢复。
    pass
