"""add role data scopes and creator fields

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-03-14 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("data_scopes", sa.JSON(), nullable=True))
    op.add_column("trainings", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("training_bases", sa.Column("created_by", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_trainings_created_by_users",
        "trainings",
        "users",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_training_bases_created_by_users",
        "training_bases",
        "users",
        ["created_by"],
        ["id"],
    )

    op.execute(sa.text("UPDATE roles SET data_scopes = '[\"all\"]'::json WHERE code = 'admin' AND data_scopes IS NULL"))
    op.execute(
        sa.text(
            "UPDATE roles SET data_scopes = '[\"department_and_sub\", \"police_type\", \"self\"]'::json "
            "WHERE code = 'instructor' AND data_scopes IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE roles SET data_scopes = '[\"department\", \"police_type\", \"self\"]'::json "
            "WHERE code = 'student' AND data_scopes IS NULL"
        )
    )
    op.execute(sa.text("UPDATE roles SET data_scopes = '[\"all\"]'::json WHERE data_scopes IS NULL"))
    op.execute(
        sa.text(
            """
            UPDATE trainings
            SET created_by = COALESCE(created_by, published_by, instructor_id)
            WHERE created_by IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_training_bases_created_by_users", "training_bases", type_="foreignkey")
    op.drop_constraint("fk_trainings_created_by_users", "trainings", type_="foreignkey")
    op.drop_column("training_bases", "created_by")
    op.drop_column("trainings", "created_by")
    op.drop_column("roles", "data_scopes")
