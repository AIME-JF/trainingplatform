"""add knowledge item ids to chat and scenarios

Revision ID: f0e1d2c3b4a5
Revises: 021f05c8dd6a
Create Date: 2026-04-09 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f0e1d2c3b4a5"
down_revision: Union[str, None] = "021f05c8dd6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "knowledge_chat_sessions",
        sa.Column("knowledge_item_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "scenario_templates",
        sa.Column("knowledge_item_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.alter_column("knowledge_chat_sessions", "knowledge_item_ids", server_default=None)
    op.alter_column("scenario_templates", "knowledge_item_ids", server_default=None)


def downgrade() -> None:
    op.drop_column("scenario_templates", "knowledge_item_ids")
    op.drop_column("knowledge_chat_sessions", "knowledge_item_ids")
