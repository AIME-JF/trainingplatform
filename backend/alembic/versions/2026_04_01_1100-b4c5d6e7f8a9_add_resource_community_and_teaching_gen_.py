"""add resource community and teaching generation permission

Revision ID: b4c5d6e7f8a9
Revises: a3d174a9a2c6
Create Date: 2026-04-01 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3d174a9a2c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEACHING_RESOURCE_PERMISSION = {
    "path": "/api/v1/ai/teaching-resource-generation-tasks",
    "code": "USE_TEACHING_RESOURCE_GENERATION",
    "group": "AI",
    "description": "使用教学资源生成功能",
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("resources"):
        resource_columns = {column["name"] for column in inspector.get_columns("resources")}
        if "share_count" not in resource_columns:
            op.add_column(
                "resources",
                sa.Column("share_count", sa.Integer(), nullable=False, server_default=sa.text("0"), comment="转发次数"),
            )
        if "comment_count" not in resource_columns:
            op.add_column(
                "resources",
                sa.Column("comment_count", sa.Integer(), nullable=False, server_default=sa.text("0"), comment="评论次数"),
            )

    if not inspector.has_table("resource_likes"):
        op.create_table(
            "resource_likes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=False, comment="资源ID"),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), comment="点赞时间"),
            sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("resource_id", "user_id", name="uq_resource_like_user"),
        )
        op.create_index("ix_resource_likes_id", "resource_likes", ["id"], unique=False)
        op.create_index("ix_resource_likes_resource_id", "resource_likes", ["resource_id"], unique=False)
        op.create_index("ix_resource_likes_user_id", "resource_likes", ["user_id"], unique=False)
        op.create_index("ix_resource_like_user_time", "resource_likes", ["user_id", "created_at"], unique=False)

    if not inspector.has_table("resource_comments"):
        op.create_table(
            "resource_comments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=False, comment="资源ID"),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="评论用户ID"),
            sa.Column("content", sa.Text(), nullable=False, comment="评论内容"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), comment="更新时间"),
            sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_resource_comments_id", "resource_comments", ["id"], unique=False)
        op.create_index("ix_resource_comments_resource_id", "resource_comments", ["resource_id"], unique=False)
        op.create_index("ix_resource_comments_user_id", "resource_comments", ["user_id"], unique=False)
        op.create_index("ix_resource_comment_resource_time", "resource_comments", ["resource_id", "created_at"], unique=False)
        op.create_index("ix_resource_comment_user_time", "resource_comments", ["user_id", "created_at"], unique=False)

    if inspector.has_table("permissions"):
        permissions_table = sa.table(
            "permissions",
            sa.column("id", sa.Integer()),
            sa.column("path", sa.String(length=200)),
            sa.column("code", sa.String(length=100)),
            sa.column("group", sa.String(length=100)),
            sa.column("description", sa.Text()),
            sa.column("is_active", sa.Boolean()),
        )
        roles_table = sa.table(
            "roles",
            sa.column("id", sa.Integer()),
            sa.column("code", sa.String(length=50)),
        )
        role_permissions_table = sa.table(
            "role_permissions",
            sa.column("role_id", sa.Integer()),
            sa.column("permission_id", sa.Integer()),
        )

        permission_row = bind.execute(
            sa.select(permissions_table.c.id).where(
                permissions_table.c.code == TEACHING_RESOURCE_PERMISSION["code"]
            )
        ).first()

        if permission_row is None:
            permission_id = bind.execute(
                sa.insert(permissions_table).values(
                    path=TEACHING_RESOURCE_PERMISSION["path"],
                    code=TEACHING_RESOURCE_PERMISSION["code"],
                    group=TEACHING_RESOURCE_PERMISSION["group"],
                    description=TEACHING_RESOURCE_PERMISSION["description"],
                    is_active=True,
                ).returning(permissions_table.c.id)
            ).scalar_one()
        else:
            permission_id = permission_row.id
            bind.execute(
                sa.update(permissions_table)
                .where(permissions_table.c.id == permission_id)
                .values(
                    path=TEACHING_RESOURCE_PERMISSION["path"],
                    group=TEACHING_RESOURCE_PERMISSION["group"],
                    description=TEACHING_RESOURCE_PERMISSION["description"],
                    is_active=True,
                )
            )

        if inspector.has_table("roles") and inspector.has_table("role_permissions"):
            role_rows = bind.execute(
                sa.select(roles_table.c.id, roles_table.c.code).where(
                    roles_table.c.code.in_(["admin", "instructor"])
                )
            ).fetchall()
            for role_row in role_rows:
                existing_role_permission = bind.execute(
                    sa.select(role_permissions_table.c.role_id).where(
                        role_permissions_table.c.role_id == role_row.id,
                        role_permissions_table.c.permission_id == permission_id,
                    )
                ).first()
                if existing_role_permission is None:
                    bind.execute(
                        sa.insert(role_permissions_table).values(
                            role_id=role_row.id,
                            permission_id=permission_id,
                        )
                    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("role_permissions") and inspector.has_table("permissions"):
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
        permission_row = bind.execute(
            sa.select(permissions_table.c.id).where(
                permissions_table.c.code == TEACHING_RESOURCE_PERMISSION["code"]
            )
        ).first()
        if permission_row is not None:
            bind.execute(
                sa.delete(role_permissions_table).where(
                    role_permissions_table.c.permission_id == permission_row.id
                )
            )
            bind.execute(
                sa.delete(permissions_table).where(
                    permissions_table.c.id == permission_row.id
                )
            )

    if inspector.has_table("resource_comments"):
        for index_name in [
            "ix_resource_comment_user_time",
            "ix_resource_comment_resource_time",
            "ix_resource_comments_user_id",
            "ix_resource_comments_resource_id",
            "ix_resource_comments_id",
        ]:
            op.drop_index(index_name, table_name="resource_comments")
        op.drop_table("resource_comments")

    if inspector.has_table("resource_likes"):
        for index_name in [
            "ix_resource_like_user_time",
            "ix_resource_likes_user_id",
            "ix_resource_likes_resource_id",
            "ix_resource_likes_id",
        ]:
            op.drop_index(index_name, table_name="resource_likes")
        op.drop_table("resource_likes")

    if inspector.has_table("resources"):
        resource_columns = {column["name"] for column in inspector.get_columns("resources")}
        if "comment_count" in resource_columns:
            op.drop_column("resources", "comment_count")
        if "share_count" in resource_columns:
            op.drop_column("resources", "share_count")
