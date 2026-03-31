"""add_question_folders

Revision ID: 1a2b3c4d5e6f
Revises: 9f8e7b6c5d4e
Create Date: 2026-03-31 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = '9f8e7b6c5d4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 检查 question_folders 表是否已存在
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'question_folders')"))
    table_exists = result.scalar()

    if not table_exists:
        # 创建 question_folders 表
        op.create_table(
            'question_folders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['parent_id'], ['question_folders.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_question_folders_id'), 'question_folders', ['id'], unique=False)

    # 检查 questions 表是否有 folder_id 列
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'folder_id')"))
    column_exists = result.scalar()

    if not column_exists:
        # 给 questions 表添加 folder_id 列
        op.add_column('questions', sa.Column('folder_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_questions_folder_id',
            'questions', 'question_folders',
            ['folder_id'], ['id']
        )

    # 检查默认文件夹是否已存在
    result = conn.execute(sa.text("SELECT COUNT(*) FROM question_folders"))
    folder_count = result.scalar()

    if folder_count == 0:
        # 插入默认文件夹
        op.execute("""
            INSERT INTO question_folders (name, parent_id, sort_order) VALUES
            ('刑事类', NULL, 1),
            ('治安类', NULL, 2),
            ('交通类', NULL, 3),
            ('综合类', NULL, 4)
        """)


def downgrade() -> None:
    op.drop_constraint('fk_questions_folder_id', 'questions', type_='foreignkey')
    op.drop_column('questions', 'folder_id')
    op.drop_index(op.f('ix_question_folders_id'), table_name='question_folders')
    op.drop_table('question_folders')
