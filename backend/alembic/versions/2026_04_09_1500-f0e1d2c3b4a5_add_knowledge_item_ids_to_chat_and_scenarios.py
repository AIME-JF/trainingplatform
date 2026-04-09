"""add knowledge item ids to chat and scenarios

Revision ID: f0e1d2c3b4a5
Revises: 021f05c8dd6a
Create Date: 2026-04-09 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "f0e1d2c3b4a5"
down_revision: Union[str, None] = "021f05c8dd6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, "knowledge_chat_sessions", "knowledge_item_ids"):
        op.add_column(
            "knowledge_chat_sessions",
            sa.Column("knowledge_item_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )
        op.alter_column("knowledge_chat_sessions", "knowledge_item_ids", server_default=None)

    inspector = inspect(bind)
    if not _has_column(inspector, "scenario_templates", "knowledge_item_ids"):
        op.add_column(
            "scenario_templates",
            sa.Column("knowledge_item_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )
        op.alter_column("scenario_templates", "knowledge_item_ids", server_default=None)


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    if _has_column(inspector, "scenario_templates", "knowledge_item_ids"):
        op.drop_column("scenario_templates", "knowledge_item_ids")
    if _has_column(inspector, "knowledge_chat_sessions", "knowledge_item_ids"):
        op.drop_column("knowledge_chat_sessions", "knowledge_item_ids")
