"""add_permission_group_field

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-10 10:30:00.000000

"""
from typing import Optional, Sequence, Tuple, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SYSTEM_PERMISSION_GROUP = "SYSTEM"
PATH_GROUP_RULES: Tuple[Tuple[str, str], ...] = (
    ("/api/v1/auth", "AUTH"),
    ("/api/v1/users", "USER_MANAGEMENT"),
    ("/api/v1/roles", "ROLE_MANAGEMENT"),
    ("/api/v1/permissions", "PERMISSION_MANAGEMENT"),
    ("/api/v1/departments", "DEPARTMENT_MANAGEMENT"),
    ("/api/v1/police-types", "POLICE_TYPE_MANAGEMENT"),
    ("/api/v1/courses", "COURSE_MANAGEMENT"),
    ("/api/v1/exams", "EXAM_MANAGEMENT"),
    ("/api/v1/questions", "QUESTION_BANK"),
    ("/api/v1/trainings", "TRAINING_MANAGEMENT"),
    ("/api/v1/certificates", "CERTIFICATE_MANAGEMENT"),
    ("/api/v1/profile", "PROFILE"),
    ("/api/v1/report", "REPORT"),
    ("/api/v1/ai", "AI"),
    ("/api/v1/talent", "TALENT"),
    ("/api/v1/dashboard", "DASHBOARD"),
    ("/api/v1/resources", "RESOURCE_REVIEW"),
    ("/api/v1/reviews", "RESOURCE_REVIEW"),
    ("/api/v1/review-policies", "RESOURCE_REVIEW"),
)


def infer_permission_group(path: Optional[str]) -> str:
    if not path:
        return SYSTEM_PERMISSION_GROUP

    normalized_path = path.strip()
    if normalized_path in {"/", "/health"}:
        return SYSTEM_PERMISSION_GROUP

    for prefix, group in PATH_GROUP_RULES:
        if normalized_path.startswith(prefix):
            return group

    return SYSTEM_PERMISSION_GROUP


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("permissions"):
        return

    columns = {col["name"] for col in inspector.get_columns("permissions")}
    if "group" not in columns:
        op.add_column(
            "permissions",
            sa.Column("group", sa.String(length=100), nullable=True, comment="权限分组"),
        )

    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("permissions")}
    if "group" not in columns:
        return

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer()),
        sa.column("path", sa.String(length=200)),
        sa.column("group", sa.String(length=100)),
    )

    pending_rows = bind.execute(
        sa.select(permissions_table.c.id, permissions_table.c.path).where(
            sa.or_(
                permissions_table.c["group"].is_(None),
                permissions_table.c["group"] == "",
            )
        )
    ).all()

    for permission_id, path in pending_rows:
        bind.execute(
            sa.update(permissions_table)
            .where(permissions_table.c.id == permission_id)
            .values({"group": infer_permission_group(path)})
        )

    op.alter_column(
        "permissions",
        "group",
        existing_type=sa.String(length=100),
        nullable=False,
        server_default=sa.text("'SYSTEM'"),
        existing_comment="权限分组",
    )

    inspector = inspect(bind)
    index_names = {idx["name"] for idx in inspector.get_indexes("permissions")}
    if "ix_permissions_group" not in index_names:
        op.create_index("ix_permissions_group", "permissions", ["group"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("permissions"):
        return

    index_names = {idx["name"] for idx in inspector.get_indexes("permissions")}
    if "ix_permissions_group" in index_names:
        op.drop_index("ix_permissions_group", table_name="permissions")

    columns = {col["name"] for col in inspector.get_columns("permissions")}
    if "group" in columns:
        op.drop_column("permissions", "group")

