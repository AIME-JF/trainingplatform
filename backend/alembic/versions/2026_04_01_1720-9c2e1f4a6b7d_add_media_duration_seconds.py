"""add media duration seconds

Revision ID: 9c2e1f4a6b7d
Revises: 3654902f12cf
Create Date: 2026-04-01 17:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "9c2e1f4a6b7d"
down_revision: Union[str, None] = "3654902f12cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("media_files"):
        columns = {column["name"] for column in inspector.get_columns("media_files")}
        if "duration_seconds" not in columns:
            op.add_column(
                "media_files",
                sa.Column(
                    "duration_seconds",
                    sa.Integer(),
                    nullable=False,
                    server_default=sa.text("0"),
                    comment="媒体时长(秒)",
                ),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("media_files"):
        columns = {column["name"] for column in inspector.get_columns("media_files")}
        if "duration_seconds" in columns:
            op.drop_column("media_files", "duration_seconds")
