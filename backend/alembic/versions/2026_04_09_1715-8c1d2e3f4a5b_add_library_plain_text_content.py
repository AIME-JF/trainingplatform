"""add library plain text content

Revision ID: 8c1d2e3f4a5b
Revises: 4b847d29017c
Create Date: 2026-04-09 17:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "8c1d2e3f4a5b"
down_revision: Union[str, None] = "4b847d29017c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, "library_items", "plain_text_content"):
        op.add_column(
            "library_items",
            sa.Column("plain_text_content", sa.Text(), nullable=True, comment="Plain text used by AI context"),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if _has_column(inspector, "library_items", "plain_text_content"):
        op.drop_column("library_items", "plain_text_content")
