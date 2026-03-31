"""add training bases and domain fields

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-03-14 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_bases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, comment="培训基地名称"),
        sa.Column("location", sa.String(length=200), nullable=False, comment="培训基地地点"),
        sa.Column("department_id", sa.Integer(), nullable=True, comment="关联部门ID"),
        sa.Column("description", sa.Text(), nullable=True, comment="备注"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_training_bases_id"), "training_bases", ["id"], unique=False)

    op.add_column("questions", sa.Column("police_type_id", sa.Integer(), nullable=True, comment="警种ID"))
    op.create_foreign_key(
        "fk_questions_police_type_id_police_types",
        "questions",
        "police_types",
        ["police_type_id"],
        ["id"],
    )

    op.add_column("trainings", sa.Column("department_id", sa.Integer(), nullable=True, comment="归属部门ID"))
    op.add_column("trainings", sa.Column("police_type_id", sa.Integer(), nullable=True, comment="警种ID"))
    op.add_column("trainings", sa.Column("training_base_id", sa.Integer(), nullable=True, comment="培训基地ID"))
    op.create_foreign_key(
        "fk_trainings_department_id_departments",
        "trainings",
        "departments",
        ["department_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_trainings_police_type_id_police_types",
        "trainings",
        "police_types",
        ["police_type_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_trainings_training_base_id_training_bases",
        "trainings",
        "training_bases",
        ["training_base_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_trainings_training_base_id_training_bases", "trainings", type_="foreignkey")
    op.drop_constraint("fk_trainings_police_type_id_police_types", "trainings", type_="foreignkey")
    op.drop_constraint("fk_trainings_department_id_departments", "trainings", type_="foreignkey")
    op.drop_column("trainings", "training_base_id")
    op.drop_column("trainings", "police_type_id")
    op.drop_column("trainings", "department_id")

    op.drop_constraint("fk_questions_police_type_id_police_types", "questions", type_="foreignkey")
    op.drop_column("questions", "police_type_id")

    op.drop_index(op.f("ix_training_bases_id"), table_name="training_bases")
    op.drop_table("training_bases")
