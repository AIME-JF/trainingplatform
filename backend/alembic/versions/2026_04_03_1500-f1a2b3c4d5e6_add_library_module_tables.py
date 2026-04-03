"""add library module tables

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-04-03 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "library_folders" not in table_names:
        op.create_table(
            "library_folders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="所属用户ID"),
            sa.Column("name", sa.String(length=100), nullable=False, comment="文件夹名称"),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("library_folders.id", ondelete="CASCADE"), nullable=True, comment="父文件夹ID"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="排序"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
            sa.UniqueConstraint("owner_user_id", "parent_id", "name", name="uq_library_folder_owner_parent_name"),
        )
        op.create_index("ix_library_folders_owner_user_id", "library_folders", ["owner_user_id"])
        op.create_index("ix_library_folders_parent_id", "library_folders", ["parent_id"])

    if "library_items" not in table_names:
        op.create_table(
            "library_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="所属用户ID"),
            sa.Column("folder_id", sa.Integer(), sa.ForeignKey("library_folders.id", ondelete="SET NULL"), nullable=True, comment="所属文件夹ID"),
            sa.Column("title", sa.String(length=200), nullable=False, comment="资源标题"),
            sa.Column("content_type", sa.String(length=20), nullable=False, comment="资源类型"),
            sa.Column("source_kind", sa.String(length=20), nullable=False, server_default="file", comment="来源类型"),
            sa.Column("media_file_id", sa.Integer(), sa.ForeignKey("media_files.id"), nullable=True, comment="关联文件ID"),
            sa.Column("knowledge_content_html", sa.Text(), nullable=True, comment="知识点富文本内容"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否公开"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        )
        op.create_index("ix_library_items_owner_user_id", "library_items", ["owner_user_id"])
        op.create_index("ix_library_items_folder_id", "library_items", ["folder_id"])

    if "chapters" in table_names:
        chapter_columns = {column["name"] for column in inspector.get_columns("chapters")}
        if "library_item_id" not in chapter_columns:
            op.add_column("chapters", sa.Column("library_item_id", sa.Integer(), nullable=True, comment="关联资源库项ID"))
            op.create_foreign_key(
                "fk_chapters_library_item_id",
                "chapters",
                "library_items",
                ["library_item_id"],
                ["id"],
            )
            op.create_index("ix_chapters_library_item_id", "chapters", ["library_item_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "chapters" in table_names:
        chapter_columns = {column["name"] for column in inspector.get_columns("chapters")}
        if "library_item_id" in chapter_columns:
            indexes = {index["name"] for index in inspector.get_indexes("chapters")}
            if "ix_chapters_library_item_id" in indexes:
                op.drop_index("ix_chapters_library_item_id", table_name="chapters")
            foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("chapters")}
            if "fk_chapters_library_item_id" in foreign_keys:
                op.drop_constraint("fk_chapters_library_item_id", "chapters", type_="foreignkey")
            op.drop_column("chapters", "library_item_id")

    if "library_items" in table_names:
        indexes = {index["name"] for index in inspector.get_indexes("library_items")}
        if "ix_library_items_folder_id" in indexes:
            op.drop_index("ix_library_items_folder_id", table_name="library_items")
        if "ix_library_items_owner_user_id" in indexes:
            op.drop_index("ix_library_items_owner_user_id", table_name="library_items")
        op.drop_table("library_items")

    if "library_folders" in table_names:
        indexes = {index["name"] for index in inspector.get_indexes("library_folders")}
        if "ix_library_folders_parent_id" in indexes:
            op.drop_index("ix_library_folders_parent_id", table_name="library_folders")
        if "ix_library_folders_owner_user_id" in indexes:
            op.drop_index("ix_library_folders_owner_user_id", table_name="library_folders")
        op.drop_table("library_folders")
