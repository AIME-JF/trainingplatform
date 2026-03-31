"""add knowledge point relation

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-03-24 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "f9a0b1c2d3e4"
down_revision: Union[str, None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QUESTION_BANK_GROUP = "QUESTION_BANK"
KNOWLEDGE_POINT_PERMISSION_DEFINITIONS = (
    {
        "path": "/api/v1/knowledge-points",
        "code": "GET_KNOWLEDGE_POINTS",
        "description": "获取知识点列表",
    },
    {
        "path": "/api/v1/knowledge-points/create",
        "code": "CREATE_KNOWLEDGE_POINT",
        "description": "创建知识点",
    },
    {
        "path": "/api/v1/knowledge-points/{id}/update",
        "code": "UPDATE_KNOWLEDGE_POINT",
        "description": "更新知识点",
    },
    {
        "path": "/api/v1/knowledge-points/{id}/delete",
        "code": "DELETE_KNOWLEDGE_POINT",
        "description": "删除知识点",
    },
)


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _ensure_knowledge_point_tables(inspector) -> None:
    if not _has_table(inspector, "knowledge_points"):
        op.create_table(
            "knowledge_points",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False, unique=True, comment="知识点名称"),
            sa.Column("description", sa.Text(), nullable=True, comment="知识点描述"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), comment="是否启用"),
            sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )

    inspector = inspect(op.get_bind())
    if not _has_table(inspector, "question_knowledge_point_relations"):
        op.create_table(
            "question_knowledge_point_relations",
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("knowledge_point_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["knowledge_point_id"], ["knowledge_points.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("question_id", "knowledge_point_id"),
        )

    inspector = inspect(op.get_bind())
    if not _has_index(inspector, "question_knowledge_point_relations", "ix_question_knowledge_point_relations_knowledge_point_id"):
        op.create_index(
            "ix_question_knowledge_point_relations_knowledge_point_id",
            "question_knowledge_point_relations",
            ["knowledge_point_id"],
            unique=False,
        )


def _ensure_snapshot_columns(inspector) -> None:
    if _has_table(inspector, "exam_paper_questions") and not _has_column(inspector, "exam_paper_questions", "knowledge_points"):
        op.add_column("exam_paper_questions", sa.Column("knowledge_points", sa.JSON(), nullable=True, comment="知识点快照"))
    if _has_table(inspector, "exam_questions") and not _has_column(inspector, "exam_questions", "knowledge_points"):
        op.add_column("exam_questions", sa.Column("knowledge_points", sa.JSON(), nullable=True, comment="知识点快照"))


def _migrate_question_knowledge_points(bind, inspector) -> None:
    if not _has_table(inspector, "questions") or not _has_column(inspector, "questions", "knowledge_point"):
        return

    questions_table = sa.table(
        "questions",
        sa.column("id", sa.Integer()),
        sa.column("knowledge_point", sa.String(length=200)),
    )
    knowledge_points_table = sa.table(
        "knowledge_points",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(length=100)),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_by", sa.Integer()),
    )
    relation_table = sa.table(
        "question_knowledge_point_relations",
        sa.column("question_id", sa.Integer()),
        sa.column("knowledge_point_id", sa.Integer()),
    )

    existing_knowledge_points = {
        row.name: row.id
        for row in bind.execute(
            sa.select(knowledge_points_table.c.id, knowledge_points_table.c.name)
        ).fetchall()
    }
    existing_relations = {
        (row.question_id, row.knowledge_point_id)
        for row in bind.execute(
            sa.select(relation_table.c.question_id, relation_table.c.knowledge_point_id)
        ).fetchall()
    }

    question_rows = bind.execute(
        sa.select(questions_table.c.id, questions_table.c.knowledge_point)
    ).fetchall()
    for row in question_rows:
        name = str(row.knowledge_point or "").strip()
        if not name:
            continue
        normalized_name = name[:100]
        knowledge_point_id = existing_knowledge_points.get(normalized_name)
        if knowledge_point_id is None:
            knowledge_point_id = bind.execute(
                sa.insert(knowledge_points_table).values(
                    name=normalized_name,
                    is_active=True,
                )
                .returning(knowledge_points_table.c.id)
            ).scalar_one()
            existing_knowledge_points[normalized_name] = knowledge_point_id
        relation_key = (row.id, knowledge_point_id)
        if relation_key in existing_relations:
            continue
        bind.execute(
            sa.insert(relation_table).values(
                question_id=row.id,
                knowledge_point_id=knowledge_point_id,
            )
        )
        existing_relations.add(relation_key)

    op.drop_column("questions", "knowledge_point")


def _migrate_snapshot_knowledge_points(bind, inspector, table_name: str, primary_keys: list[str]) -> None:
    if not _has_table(inspector, table_name):
        return
    if not _has_column(inspector, table_name, "knowledge_points") or not _has_column(inspector, table_name, "knowledge_point"):
        return

    snapshot_table = sa.table(
        table_name,
        *(sa.column(primary_key, sa.Integer()) for primary_key in primary_keys),
        sa.column("knowledge_point", sa.String(length=200)),
        sa.column("knowledge_points", sa.JSON()),
    )

    query_columns = [getattr(snapshot_table.c, primary_key) for primary_key in primary_keys]
    query_columns.extend([snapshot_table.c.knowledge_point, snapshot_table.c.knowledge_points])
    rows = bind.execute(sa.select(*query_columns)).fetchall()
    for row in rows:
        knowledge_points = row.knowledge_points
        if knowledge_points not in (None, []):
            continue
        knowledge_point = str(row.knowledge_point or "").strip()
        if not knowledge_point:
            continue

        where_clause = sa.and_(*[
            getattr(snapshot_table.c, primary_key) == getattr(row, primary_key)
            for primary_key in primary_keys
        ])
        bind.execute(
            sa.update(snapshot_table)
            .where(where_clause)
            .values(knowledge_points=[knowledge_point])
        )

    op.drop_column(table_name, "knowledge_point")


def _sync_permission_data(bind, inspector) -> None:
    if not _has_table(inspector, "permissions"):
        return

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

    existing_permissions = {
        row.code: row.id
        for row in bind.execute(
            sa.select(
                permissions_table.c.id,
                permissions_table.c.code,
            )
        ).fetchall()
    }
    for item in KNOWLEDGE_POINT_PERMISSION_DEFINITIONS:
        values = {
            "path": item["path"],
            "code": item["code"],
            "group": QUESTION_BANK_GROUP,
            "description": item["description"],
            "is_active": True,
        }
        permission_id = existing_permissions.get(item["code"])
        if permission_id is None:
            permission_id = bind.execute(
                sa.insert(permissions_table).values(values).returning(permissions_table.c.id)
            ).scalar_one()
            existing_permissions[item["code"]] = permission_id
            continue
        bind.execute(
            sa.update(permissions_table)
            .where(permissions_table.c.id == permission_id)
            .values(values)
        )

    if not _has_table(inspector, "roles") or not _has_table(inspector, "role_permissions"):
        return

    permission_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.select(
                permissions_table.c.id,
                permissions_table.c.code,
            ).where(
                permissions_table.c.code.in_([item["code"] for item in KNOWLEDGE_POINT_PERMISSION_DEFINITIONS])
            )
        ).fetchall()
    }
    role_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.select(roles_table.c.id, roles_table.c.code).where(
                roles_table.c.code.in_(["admin", "instructor"])
            )
        ).fetchall()
    }
    for role_id in role_ids.values():
        existing_permission_ids = {
            row.permission_id
            for row in bind.execute(
                sa.select(role_permissions_table.c.permission_id).where(
                    role_permissions_table.c.role_id == role_id
                )
            ).fetchall()
        }
        for permission_code in permission_ids:
            permission_id = permission_ids[permission_code]
            if permission_id in existing_permission_ids:
                continue
            bind.execute(
                sa.insert(role_permissions_table).values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _ensure_knowledge_point_tables(inspector)
    inspector = inspect(bind)
    _ensure_snapshot_columns(inspector)
    inspector = inspect(bind)

    _migrate_question_knowledge_points(bind, inspector)
    inspector = inspect(bind)
    _migrate_snapshot_knowledge_points(bind, inspector, "exam_paper_questions", ["paper_id", "question_id"])
    inspector = inspect(bind)
    _migrate_snapshot_knowledge_points(bind, inspector, "exam_questions", ["exam_id", "question_id"])
    inspector = inspect(bind)

    _sync_permission_data(bind, inspector)


def downgrade() -> None:
    # 本次迁移包含数据搬迁，降级保持非破坏性处理。
    pass
