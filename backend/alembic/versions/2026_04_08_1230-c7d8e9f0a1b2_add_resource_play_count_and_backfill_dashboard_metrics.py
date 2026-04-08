"""add resource play_count and backfill dashboard metrics

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-04-08 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "b6c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _set_all_resources_counter(column_name: str, value: int = 0) -> None:
    op.execute(sa.text(f"UPDATE resources SET {column_name} = :value").bindparams(value=value))


def _backfill_counter_from_grouped_table(column_name: str, source_table: str, where_clause: str = "") -> None:
    where_sql = f"WHERE {where_clause}" if where_clause else ""
    op.execute(sa.text(f"""
        UPDATE resources AS r
        SET {column_name} = src.total
        FROM (
            SELECT resource_id, COUNT(*)::int AS total
            FROM {source_table}
            {where_sql}
            GROUP BY resource_id
        ) AS src
        WHERE r.id = src.resource_id
    """))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("resources"):
        return

    resource_columns = {column["name"] for column in inspector.get_columns("resources")}
    if "play_count" not in resource_columns:
        op.add_column(
            "resources",
            sa.Column("play_count", sa.Integer(), nullable=False, server_default=sa.text("0"), comment="播放次数"),
        )
        resource_columns.add("play_count")

    for counter_column in ("view_count", "play_count", "like_count", "share_count", "comment_count", "favorite_count"):
        if counter_column in resource_columns:
            _set_all_resources_counter(counter_column, 0)

    if inspector.has_table("resource_behavior_events"):
        if "view_count" in resource_columns:
            _backfill_counter_from_grouped_table("view_count", "resource_behavior_events", "event_type = 'click'")
        if "play_count" in resource_columns:
            _backfill_counter_from_grouped_table("play_count", "resource_behavior_events", "event_type = 'play'")
        if "share_count" in resource_columns:
            _backfill_counter_from_grouped_table("share_count", "resource_behavior_events", "event_type = 'share'")
        if "favorite_count" in resource_columns:
            _backfill_counter_from_grouped_table("favorite_count", "resource_behavior_events", "event_type = 'favorite'")

    if inspector.has_table("resource_likes") and "like_count" in resource_columns:
        _backfill_counter_from_grouped_table("like_count", "resource_likes")

    if inspector.has_table("resource_comments") and "comment_count" in resource_columns:
        _backfill_counter_from_grouped_table("comment_count", "resource_comments")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("resources"):
        return

    resource_columns = {column["name"] for column in inspector.get_columns("resources")}
    if "play_count" in resource_columns:
        op.drop_column("resources", "play_count")
