"""add_paper_folders

Revision ID: 9f8e7b6c5d4e
Revises: 209e778b7e3f
Create Date: 2026-03-31 16:31:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f8e7b6c5d4e'
down_revision = '209e778b7e3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查 paper_folders 表是否已存在
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'paper_folders')"))
    table_exists = result.scalar()

    if not table_exists:
        # 创建 paper_folders 表
        op.create_table(
            'paper_folders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['parent_id'], ['paper_folders.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_paper_folders_id'), 'paper_folders', ['id'], unique=False)

    # 检查 exam_papers 表是否有 folder_id 列
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'exam_papers' AND column_name = 'folder_id')"))
    column_exists = result.scalar()

    if not column_exists:
        # 给 exam_papers 表添加 folder_id 列
        op.add_column('exam_papers', sa.Column('folder_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_exam_papers_folder_id',
            'exam_papers', 'paper_folders',
            ['folder_id'], ['id']
        )

    # 检查默认文件夹是否已存在
    result = conn.execute(sa.text("SELECT COUNT(*) FROM paper_folders"))
    folder_count = result.scalar()

    if folder_count == 0:
        # 插入默认文件夹
        op.execute("""
            INSERT INTO paper_folders (name, parent_id, sort_order) VALUES
            ('刑事类', NULL, 1),
            ('治安类', NULL, 2),
            ('交通类', NULL, 3),
            ('综合类', NULL, 4)
        """)


def downgrade() -> None:
    op.drop_constraint('fk_exam_papers_folder_id', 'exam_papers', type_='foreignkey')
    op.drop_column('exam_papers', 'folder_id')
    op.drop_index(op.f('ix_paper_folders_id'), table_name='paper_folders')
    op.drop_table('paper_folders')
