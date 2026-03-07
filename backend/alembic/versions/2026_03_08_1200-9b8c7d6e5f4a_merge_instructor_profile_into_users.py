"""merge instructor profile into users

Revision ID: 9b8c7d6e5f4a
Revises: ef0e16b5cafc
Create Date: 2026-03-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9b8c7d6e5f4a'
down_revision: Union[str, None] = 'ef0e16b5cafc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('users'):
        user_columns = {col['name'] for col in inspector.get_columns('users')}

        if 'instructor_title' not in user_columns:
            op.add_column('users', sa.Column('instructor_title', sa.String(length=50), nullable=True, comment='教官职称'))
        if 'instructor_level' not in user_columns:
            op.add_column('users', sa.Column('instructor_level', sa.String(length=20), nullable=True, comment='教官等级'))
        if 'instructor_specialties' not in user_columns:
            op.add_column('users', sa.Column('instructor_specialties', sa.JSON(), nullable=True, comment='教官专长数组'))
        if 'instructor_qualification' not in user_columns:
            op.add_column('users', sa.Column('instructor_qualification', sa.JSON(), nullable=True, comment='教官资质数组'))
        if 'instructor_certificates' not in user_columns:
            op.add_column('users', sa.Column('instructor_certificates', sa.JSON(), nullable=True, comment='教官证书列表'))
        if 'instructor_intro' not in user_columns:
            op.add_column('users', sa.Column('instructor_intro', sa.Text(), nullable=True, comment='教官简介'))
        if 'instructor_rating' not in user_columns:
            op.add_column(
                'users',
                sa.Column('instructor_rating', sa.Float(), nullable=False, server_default=sa.text('0'), comment='教官评分')
            )
        if 'instructor_course_count' not in user_columns:
            op.add_column(
                'users',
                sa.Column('instructor_course_count', sa.Integer(), nullable=False, server_default=sa.text('0'), comment='教官课程数')
            )
        if 'instructor_student_count' not in user_columns:
            op.add_column(
                'users',
                sa.Column('instructor_student_count', sa.Integer(), nullable=False, server_default=sa.text('0'), comment='教官学员数')
            )
        if 'instructor_review_count' not in user_columns:
            op.add_column(
                'users',
                sa.Column('instructor_review_count', sa.Integer(), nullable=False, server_default=sa.text('0'), comment='教官评价数')
            )

    inspector = inspect(bind)
    if inspector.has_table('instructor_profiles') and inspector.has_table('users'):
        user_columns = {col['name'] for col in inspector.get_columns('users')}
        profile_columns = {col['name'] for col in inspector.get_columns('instructor_profiles')}

        required_user_columns = {
            'instructor_title', 'instructor_level', 'instructor_specialties',
            'instructor_qualification', 'instructor_certificates', 'instructor_intro',
            'instructor_rating', 'instructor_course_count', 'instructor_student_count',
            'instructor_review_count'
        }
        required_profile_columns = {
            'user_id', 'title', 'level', 'specialties', 'qualification',
            'certificates', 'intro', 'rating', 'course_count', 'student_count',
            'review_count'
        }

        if required_user_columns.issubset(user_columns) and required_profile_columns.issubset(profile_columns):
            op.execute(
                """
                UPDATE users AS u
                SET
                    instructor_title = ip.title,
                    instructor_level = ip.level,
                    instructor_specialties = ip.specialties,
                    instructor_qualification = ip.qualification,
                    instructor_certificates = ip.certificates,
                    instructor_intro = ip.intro,
                    instructor_rating = COALESCE(ip.rating, 0),
                    instructor_course_count = COALESCE(ip.course_count, 0),
                    instructor_student_count = COALESCE(ip.student_count, 0),
                    instructor_review_count = COALESCE(ip.review_count, 0)
                FROM instructor_profiles AS ip
                WHERE u.id = ip.user_id
                """
            )

        op.drop_table('instructor_profiles')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('instructor_profiles'):
        op.create_table(
            'instructor_profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
            sa.Column('title', sa.String(length=50), nullable=True, comment='职称: 高级教官/中级教官/初级教官'),
            sa.Column('level', sa.String(length=20), nullable=True, comment='等级: expert/senior/standard'),
            sa.Column('specialties', sa.JSON(), nullable=True, comment='专长数组'),
            sa.Column('qualification', sa.JSON(), nullable=True, comment='资质数组'),
            sa.Column('certificates', sa.JSON(), nullable=True, comment='证书列表 [{name,issuer,year}]'),
            sa.Column('intro', sa.Text(), nullable=True, comment='简介'),
            sa.Column('rating', sa.Float(), nullable=True, server_default=sa.text('0'), comment='评分'),
            sa.Column('course_count', sa.Integer(), nullable=True, server_default=sa.text('0'), comment='课程数'),
            sa.Column('student_count', sa.Integer(), nullable=True, server_default=sa.text('0'), comment='学员数'),
            sa.Column('review_count', sa.Integer(), nullable=True, server_default=sa.text('0'), comment='评价数'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        op.create_index(op.f('ix_instructor_profiles_id'), 'instructor_profiles', ['id'], unique=False)

    inspector = inspect(bind)
    if inspector.has_table('users') and inspector.has_table('instructor_profiles'):
        user_columns = {col['name'] for col in inspector.get_columns('users')}
        required_user_columns = {
            'instructor_title', 'instructor_level', 'instructor_specialties',
            'instructor_qualification', 'instructor_certificates', 'instructor_intro',
            'instructor_rating', 'instructor_course_count', 'instructor_student_count',
            'instructor_review_count'
        }

        if required_user_columns.issubset(user_columns):
            op.execute(
                """
                INSERT INTO instructor_profiles (
                    user_id, title, level, specialties, qualification, certificates, intro,
                    rating, course_count, student_count, review_count
                )
                SELECT
                    u.id,
                    u.instructor_title,
                    u.instructor_level,
                    u.instructor_specialties,
                    u.instructor_qualification,
                    u.instructor_certificates,
                    u.instructor_intro,
                    COALESCE(u.instructor_rating, 0),
                    COALESCE(u.instructor_course_count, 0),
                    COALESCE(u.instructor_student_count, 0),
                    COALESCE(u.instructor_review_count, 0)
                FROM users AS u
                WHERE (
                    u.instructor_title IS NOT NULL OR
                    u.instructor_level IS NOT NULL OR
                    u.instructor_specialties IS NOT NULL OR
                    u.instructor_qualification IS NOT NULL OR
                    u.instructor_certificates IS NOT NULL OR
                    u.instructor_intro IS NOT NULL OR
                    COALESCE(u.instructor_rating, 0) <> 0 OR
                    COALESCE(u.instructor_course_count, 0) <> 0 OR
                    COALESCE(u.instructor_student_count, 0) <> 0 OR
                    COALESCE(u.instructor_review_count, 0) <> 0
                )
                AND NOT EXISTS (
                    SELECT 1 FROM instructor_profiles ip WHERE ip.user_id = u.id
                )
                """
            )

    inspector = inspect(bind)
    if inspector.has_table('users'):
        user_columns = {col['name'] for col in inspector.get_columns('users')}

        if 'instructor_review_count' in user_columns:
            op.drop_column('users', 'instructor_review_count')
        if 'instructor_student_count' in user_columns:
            op.drop_column('users', 'instructor_student_count')
        if 'instructor_course_count' in user_columns:
            op.drop_column('users', 'instructor_course_count')
        if 'instructor_rating' in user_columns:
            op.drop_column('users', 'instructor_rating')
        if 'instructor_intro' in user_columns:
            op.drop_column('users', 'instructor_intro')
        if 'instructor_certificates' in user_columns:
            op.drop_column('users', 'instructor_certificates')
        if 'instructor_qualification' in user_columns:
            op.drop_column('users', 'instructor_qualification')
        if 'instructor_specialties' in user_columns:
            op.drop_column('users', 'instructor_specialties')
        if 'instructor_level' in user_columns:
            op.drop_column('users', 'instructor_level')
        if 'instructor_title' in user_columns:
            op.drop_column('users', 'instructor_title')
