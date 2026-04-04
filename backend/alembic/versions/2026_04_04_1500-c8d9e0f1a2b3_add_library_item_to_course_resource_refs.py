"""add library item support to course resource refs

Revision ID: c8d9e0f1a2b3
Revises: f1a2b3c4d5e6
Create Date: 2026-04-04 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "course_resource_refs" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("course_resource_refs")}
    indexes = {index["name"] for index in inspector.get_indexes("course_resource_refs")}
    foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("course_resource_refs")}
    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("course_resource_refs")}

    if "library_item_id" not in columns:
        op.add_column(
            "course_resource_refs",
            sa.Column("library_item_id", sa.Integer(), nullable=True, comment="关联资源库项ID"),
        )

    if "ix_course_resource_refs_library_item_id" not in indexes:
        op.create_index("ix_course_resource_refs_library_item_id", "course_resource_refs", ["library_item_id"])

    if "fk_course_resource_refs_library_item_id" not in foreign_keys:
        op.create_foreign_key(
            "fk_course_resource_refs_library_item_id",
            "course_resource_refs",
            "library_items",
            ["library_item_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if "uq_course_library_item_ref" not in unique_constraints:
        op.create_unique_constraint(
            "uq_course_library_item_ref",
            "course_resource_refs",
            ["course_id", "library_item_id"],
        )

    if "resource_id" in columns:
        op.alter_column(
            "course_resource_refs",
            "resource_id",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "course_resource_refs" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("course_resource_refs")}
    indexes = {index["name"] for index in inspector.get_indexes("course_resource_refs")}
    foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("course_resource_refs")}
    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("course_resource_refs")}

    if "library_item_id" in columns:
        course_resource_refs = sa.table(
            "course_resource_refs",
            sa.column("library_item_id", sa.Integer()),
            sa.column("resource_id", sa.Integer()),
        )
        bind.execute(
            sa.delete(course_resource_refs).where(
                course_resource_refs.c.library_item_id.is_not(None),
                course_resource_refs.c.resource_id.is_(None),
            )
        )

    if "resource_id" in columns:
        op.alter_column(
            "course_resource_refs",
            "resource_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    if "uq_course_library_item_ref" in unique_constraints:
        op.drop_constraint("uq_course_library_item_ref", "course_resource_refs", type_="unique")

    if "fk_course_resource_refs_library_item_id" in foreign_keys:
        op.drop_constraint("fk_course_resource_refs_library_item_id", "course_resource_refs", type_="foreignkey")

    if "ix_course_resource_refs_library_item_id" in indexes:
        op.drop_index("ix_course_resource_refs_library_item_id", table_name="course_resource_refs")

    if "library_item_id" in columns:
        op.drop_column("course_resource_refs", "library_item_id")
