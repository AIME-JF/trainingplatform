"""add knowledge_base and scenario models

Revision ID: 021f05c8dd6a
Revises: 5fef50b2313e
Create Date: 2026-04-09 09:00:27.980327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '021f05c8dd6a'
down_revision: Union[str, None] = '5fef50b2313e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_existing_indexes(inspector, table_name: str) -> set[str]:
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _create_missing_indexes(inspector) -> None:
    index_specs: dict[str, list[tuple[str, list[str]]]] = {
        "knowledge_bases": [
            ("ix_knowledge_bases_created_by", ["created_by"]),
            ("ix_knowledge_bases_id", ["id"]),
        ],
        "knowledge_chat_sessions": [
            ("ix_knowledge_chat_sessions_id", ["id"]),
            ("ix_knowledge_chat_sessions_knowledge_base_id", ["knowledge_base_id"]),
            ("ix_knowledge_chat_sessions_user_id", ["user_id"]),
        ],
        "knowledge_documents": [
            ("ix_knowledge_documents_created_by", ["created_by"]),
            ("ix_knowledge_documents_id", ["id"]),
            ("ix_knowledge_documents_knowledge_base_id", ["knowledge_base_id"]),
        ],
        "scenario_templates": [
            ("ix_scenario_templates_category", ["category"]),
            ("ix_scenario_templates_created_by", ["created_by"]),
            ("ix_scenario_templates_id", ["id"]),
            ("ix_scenario_templates_status", ["status"]),
        ],
        "scenario_sessions": [
            ("ix_scenario_sessions_id", ["id"]),
            ("ix_scenario_sessions_scenario_template_id", ["scenario_template_id"]),
            ("ix_scenario_sessions_user_id", ["user_id"]),
        ],
    }

    for table_name, indexes in index_specs.items():
        existing_indexes = _get_existing_indexes(inspector, table_name)
        for index_name, columns in indexes:
            if index_name in existing_indexes:
                continue
            op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("knowledge_bases"):
        op.create_table(
            "knowledge_bases",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False, comment="知识库名称"),
            sa.Column("description", sa.Text(), nullable=True, comment="知识库描述"),
            sa.Column("visibility", sa.String(length=20), nullable=False, comment="可见范围: all/instructor/admin"),
            sa.Column("document_count", sa.Integer(), nullable=False, comment="文档数量"),
            sa.Column("usage_count", sa.Integer(), nullable=False, comment="引用次数"),
            sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人 ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="更新时间"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("knowledge_chat_sessions"):
        op.create_table(
            "knowledge_chat_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="用户 ID"),
            sa.Column("knowledge_base_id", sa.Integer(), nullable=True, comment="关联知识库 ID"),
            sa.Column("mode", sa.String(length=20), nullable=False, comment="对话模式: qa/generate/case"),
            sa.Column("messages", sa.JSON(), nullable=False, comment="对话消息列表"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="更新时间"),
            sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("knowledge_documents"):
        op.create_table(
            "knowledge_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("knowledge_base_id", sa.Integer(), nullable=False, comment="所属知识库 ID"),
            sa.Column("title", sa.String(length=500), nullable=False, comment="文档标题"),
            sa.Column("content", sa.Text(), nullable=False, comment="文档全文内容"),
            sa.Column("source_type", sa.String(length=20), nullable=False, comment="来源类型: manual/import/ai_generated"),
            sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人 ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="更新时间"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("scenario_templates"):
        op.create_table(
            "scenario_templates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=300), nullable=False, comment="场景名称"),
            sa.Column("description", sa.Text(), nullable=True, comment="场景描述"),
            sa.Column("category", sa.String(length=30), nullable=False, comment="场景分类: law_enforcement/record_taking/law_application"),
            sa.Column("difficulty", sa.Integer(), nullable=False, comment="难度等级 1-5"),
            sa.Column("estimated_minutes", sa.Integer(), nullable=False, comment="预计时长(分钟)"),
            sa.Column("background", sa.Text(), nullable=False, comment="场景背景描述"),
            sa.Column("npc_role", sa.Text(), nullable=False, comment="AI 扮演角色描述"),
            sa.Column("npc_name", sa.String(length=50), nullable=True, comment="AI 角色名称"),
            sa.Column("npc_opening", sa.Text(), nullable=True, comment="AI 开场白"),
            sa.Column("knowledge_base_id", sa.Integer(), nullable=True, comment="关联知识库 ID"),
            sa.Column("checkpoints", sa.JSON(), nullable=False, comment="考察要点 [{label, score}]"),
            sa.Column("status", sa.String(length=20), nullable=False, comment="状态: draft/published/archived"),
            sa.Column("usage_count", sa.Integer(), nullable=False, comment="使用次数"),
            sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人 ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="更新时间"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("scenario_sessions"):
        op.create_table(
            "scenario_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("scenario_template_id", sa.Integer(), nullable=False, comment="场景模板 ID"),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="用户 ID"),
            sa.Column("messages", sa.JSON(), nullable=False, comment="对话消息列表 [{role, content, npc_name?}]"),
            sa.Column("status", sa.String(length=20), nullable=False, comment="状态: in_progress/completed"),
            sa.Column("score", sa.Integer(), nullable=True, comment="综合评分 0-100"),
            sa.Column("checkpoint_results", sa.JSON(), nullable=True, comment="考察要点结果 [{label, passed}]"),
            sa.Column("feedback", sa.Text(), nullable=True, comment="AI 评价反馈"),
            sa.Column("duration_minutes", sa.Integer(), nullable=True, comment="用时(分钟)"),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="开始时间"),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
            sa.ForeignKeyConstraint(["scenario_template_id"], ["scenario_templates.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = inspect(bind)
    _create_missing_indexes(inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_indexes: dict[str, list[str]] = {
        "scenario_sessions": [
            "ix_scenario_sessions_user_id",
            "ix_scenario_sessions_scenario_template_id",
            "ix_scenario_sessions_id",
        ],
        "scenario_templates": [
            "ix_scenario_templates_status",
            "ix_scenario_templates_id",
            "ix_scenario_templates_created_by",
            "ix_scenario_templates_category",
        ],
        "knowledge_documents": [
            "ix_knowledge_documents_knowledge_base_id",
            "ix_knowledge_documents_id",
            "ix_knowledge_documents_created_by",
        ],
        "knowledge_chat_sessions": [
            "ix_knowledge_chat_sessions_user_id",
            "ix_knowledge_chat_sessions_knowledge_base_id",
            "ix_knowledge_chat_sessions_id",
        ],
        "knowledge_bases": [
            "ix_knowledge_bases_id",
            "ix_knowledge_bases_created_by",
        ],
    }

    for table_name, index_names in table_indexes.items():
        existing_indexes = _get_existing_indexes(inspector, table_name)
        for index_name in index_names:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name=table_name)

    if inspector.has_table("scenario_sessions"):
        op.drop_table("scenario_sessions")
    if inspector.has_table("scenario_templates"):
        op.drop_table("scenario_templates")
    if inspector.has_table("knowledge_documents"):
        op.drop_table("knowledge_documents")
    if inspector.has_table("knowledge_chat_sessions"):
        op.drop_table("knowledge_chat_sessions")
    if inspector.has_table("knowledge_bases"):
        op.drop_table("knowledge_bases")
