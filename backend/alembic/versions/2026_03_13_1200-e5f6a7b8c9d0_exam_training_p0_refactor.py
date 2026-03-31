"""exam_training_p0_refactor

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-13 12:00:00.000000

"""
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _has_fk(inspector, table_name: str, constrained_columns: list[str]) -> bool:
    if not inspector.has_table(table_name):
        return False
    for fk in inspector.get_foreign_keys(table_name):
        if fk.get("constrained_columns") == constrained_columns:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("exam_papers"):
        op.create_table(
            "exam_papers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False, comment="试卷标题"),
            sa.Column("description", sa.Text(), nullable=True, comment="试卷描述"),
            sa.Column("duration", sa.Integer(), nullable=False, server_default=sa.text("60"), comment="考试时长(分钟)"),
            sa.Column("total_score", sa.Integer(), nullable=False, server_default=sa.text("100"), comment="总分"),
            sa.Column("passing_score", sa.Integer(), nullable=False, server_default=sa.text("60"), comment="及格分"),
            sa.Column("type", sa.String(length=50), nullable=False, server_default=sa.text("'formal'"), comment="试卷类型"),
            sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )

    inspector = inspect(bind)
    if not inspector.has_table("exam_paper_questions"):
        op.create_table(
            "exam_paper_questions",
            sa.Column("paper_id", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("question_type", sa.String(length=20), nullable=True, comment="题目类型快照"),
            sa.Column("content", sa.Text(), nullable=True, comment="题干快照"),
            sa.Column("options", sa.JSON(), nullable=True, comment="选项快照"),
            sa.Column("answer", sa.JSON(), nullable=True, comment="答案快照"),
            sa.Column("explanation", sa.Text(), nullable=True, comment="解析快照"),
            sa.Column("score", sa.Integer(), nullable=True, comment="分值快照"),
            sa.Column("knowledge_point", sa.String(length=200), nullable=True, comment="知识点快照"),
            sa.ForeignKeyConstraint(["paper_id"], ["exam_papers.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("paper_id", "question_id"),
        )
    else:
        paper_question_columns = {column["name"] for column in inspector.get_columns("exam_paper_questions")}
        for name, column in (
            ("question_type", sa.Column("question_type", sa.String(length=20), nullable=True, comment="题目类型快照")),
            ("content", sa.Column("content", sa.Text(), nullable=True, comment="题干快照")),
            ("options", sa.Column("options", sa.JSON(), nullable=True, comment="选项快照")),
            ("answer", sa.Column("answer", sa.JSON(), nullable=True, comment="答案快照")),
            ("explanation", sa.Column("explanation", sa.Text(), nullable=True, comment="解析快照")),
            ("score", sa.Column("score", sa.Integer(), nullable=True, comment="分值快照")),
            ("knowledge_point", sa.Column("knowledge_point", sa.String(length=200), nullable=True, comment="知识点快照")),
        ):
            if name not in paper_question_columns:
                op.add_column("exam_paper_questions", column)

    inspector = inspect(bind)
    if not inspector.has_table("admission_exams"):
        op.create_table(
            "admission_exams",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("paper_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("duration", sa.Integer(), nullable=False, server_default=sa.text("60")),
            sa.Column("total_score", sa.Integer(), nullable=False, server_default=sa.text("100")),
            sa.Column("passing_score", sa.Integer(), nullable=False, server_default=sa.text("60")),
            sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'upcoming'")),
            sa.Column("type", sa.String(length=50), nullable=False, server_default=sa.text("'formal'")),
            sa.Column("scope", sa.String(length=200), nullable=True),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["paper_id"], ["exam_papers.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )

    inspector = inspect(bind)
    if not inspector.has_table("admission_exam_records"):
        op.create_table(
            "admission_exam_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("admission_exam_id", sa.Integer(), nullable=False),
            sa.Column("paper_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("attempt_no", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'submitted'")),
            sa.Column("score", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("result", sa.String(length=20), nullable=True),
            sa.Column("grade", sa.String(length=5), nullable=True),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("answers", sa.JSON(), nullable=True),
            sa.Column("correct_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("wrong_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("wrong_questions", sa.JSON(), nullable=True),
            sa.Column("wrong_question_details", sa.JSON(), nullable=True),
            sa.Column("dimension_scores", sa.JSON(), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_exam_id"], ["admission_exams.id"]),
            sa.ForeignKeyConstraint(["paper_id"], ["exam_papers.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )

    inspector = inspect(bind)
    exam_columns = {column["name"] for column in inspector.get_columns("exams")} if inspector.has_table("exams") else set()
    if "paper_id" not in exam_columns:
        op.add_column("exams", sa.Column("paper_id", sa.Integer(), nullable=True, comment="试卷ID"))
    if "purpose" not in exam_columns:
        op.add_column("exams", sa.Column("purpose", sa.String(length=50), nullable=True, server_default=sa.text("'class_assessment'"), comment="用途"))
    if "training_id" not in exam_columns:
        op.add_column("exams", sa.Column("training_id", sa.Integer(), nullable=True, comment="关联培训班ID"))
    if "max_attempts" not in exam_columns:
        op.add_column("exams", sa.Column("max_attempts", sa.Integer(), nullable=True, server_default=sa.text("1"), comment="最大作答次数"))
    if "allow_makeup" not in exam_columns:
        op.add_column("exams", sa.Column("allow_makeup", sa.Boolean(), nullable=True, server_default=sa.false(), comment="是否允许补考"))
    if "published_at" not in exam_columns:
        op.add_column("exams", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间"))

    inspector = inspect(bind)
    if not _has_fk(inspector, "exams", ["paper_id"]):
        op.create_foreign_key("fk_exams_paper_id", "exams", "exam_papers", ["paper_id"], ["id"])
    if not _has_fk(inspector, "exams", ["training_id"]):
        op.create_foreign_key("fk_exams_training_id", "exams", "trainings", ["training_id"], ["id"])
    if not _has_index(inspector, "exams", "ix_exams_paper_id"):
        op.create_index("ix_exams_paper_id", "exams", ["paper_id"], unique=False)
    if not _has_index(inspector, "exams", "ix_exams_training_id"):
        op.create_index("ix_exams_training_id", "exams", ["training_id"], unique=False)

    inspector = inspect(bind)
    if inspector.has_table("exam_questions"):
        for fk in inspector.get_foreign_keys("exam_questions"):
            if fk.get("referred_table") == "questions" and fk.get("constrained_columns") == ["question_id"] and fk.get("name"):
                op.drop_constraint(fk["name"], "exam_questions", type_="foreignkey")

        question_columns = {column["name"] for column in inspector.get_columns("exam_questions")}
        if "question_type" not in question_columns:
            op.add_column("exam_questions", sa.Column("question_type", sa.String(length=20), nullable=True, comment="题目类型"))
        if "content" not in question_columns:
            op.add_column("exam_questions", sa.Column("content", sa.Text(), nullable=True, comment="题干快照"))
        if "options" not in question_columns:
            op.add_column("exam_questions", sa.Column("options", sa.JSON(), nullable=True, comment="选项快照"))
        if "answer" not in question_columns:
            op.add_column("exam_questions", sa.Column("answer", sa.JSON(), nullable=True, comment="答案快照"))
        if "explanation" not in question_columns:
            op.add_column("exam_questions", sa.Column("explanation", sa.Text(), nullable=True, comment="解析快照"))
        if "score" not in question_columns:
            op.add_column("exam_questions", sa.Column("score", sa.Integer(), nullable=True, comment="分值快照"))
        if "knowledge_point" not in question_columns:
            op.add_column("exam_questions", sa.Column("knowledge_point", sa.String(length=200), nullable=True, comment="知识点快照"))

    inspector = inspect(bind)
    record_columns = {column["name"] for column in inspector.get_columns("exam_records")} if inspector.has_table("exam_records") else set()
    if "paper_id" not in record_columns:
        op.add_column("exam_records", sa.Column("paper_id", sa.Integer(), nullable=True, comment="试卷ID"))
    if "attempt_no" not in record_columns:
        op.add_column("exam_records", sa.Column("attempt_no", sa.Integer(), nullable=True, server_default=sa.text("1"), comment="第几次作答"))
    if "status" not in record_columns:
        op.add_column("exam_records", sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'submitted'"), comment="作答状态"))
    if "wrong_question_details" not in record_columns:
        op.add_column("exam_records", sa.Column("wrong_question_details", sa.JSON(), nullable=True, comment="错题详情快照"))
    if "submitted_at" not in record_columns:
        op.add_column("exam_records", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"), comment="提交时间"))

    inspector = inspect(bind)
    if not _has_fk(inspector, "exam_records", ["paper_id"]):
        op.create_foreign_key("fk_exam_records_paper_id", "exam_records", "exam_papers", ["paper_id"], ["id"])
    if not _has_index(inspector, "exam_records", "ix_exam_records_paper_id"):
        op.create_index("ix_exam_records_paper_id", "exam_records", ["paper_id"], unique=False)

    inspector = inspect(bind)
    training_columns = {column["name"] for column in inspector.get_columns("trainings")} if inspector.has_table("trainings") else set()
    if "publish_status" not in training_columns:
        op.add_column("trainings", sa.Column("publish_status", sa.String(length=20), nullable=True, server_default=sa.text("'draft'"), comment="发布状态"))
    if "class_code" not in training_columns:
        op.add_column("trainings", sa.Column("class_code", sa.String(length=100), nullable=True, comment="班次编号"))
    if "published_by" not in training_columns:
        op.add_column("trainings", sa.Column("published_by", sa.Integer(), nullable=True, comment="发布人ID"))
    if "locked_by" not in training_columns:
        op.add_column("trainings", sa.Column("locked_by", sa.Integer(), nullable=True, comment="锁定人ID"))
    if "admission_exam_id" not in training_columns:
        op.add_column("trainings", sa.Column("admission_exam_id", sa.Integer(), nullable=True, comment="准入考试场次ID"))
    if "enrollment_start_at" not in training_columns:
        op.add_column("trainings", sa.Column("enrollment_start_at", sa.DateTime(timezone=True), nullable=True, comment="报名开始时间"))
    if "enrollment_end_at" not in training_columns:
        op.add_column("trainings", sa.Column("enrollment_end_at", sa.DateTime(timezone=True), nullable=True, comment="报名截止时间"))
    if "published_at" not in training_columns:
        op.add_column("trainings", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间"))
    if "locked_at" not in training_columns:
        op.add_column("trainings", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True, comment="名单锁定时间"))

    inspector = inspect(bind)
    if not _has_fk(inspector, "trainings", ["published_by"]):
        op.create_foreign_key("fk_trainings_published_by", "trainings", "users", ["published_by"], ["id"])
    if not _has_fk(inspector, "trainings", ["locked_by"]):
        op.create_foreign_key("fk_trainings_locked_by", "trainings", "users", ["locked_by"], ["id"])
    for fk in inspector.get_foreign_keys("trainings"):
        if fk.get("constrained_columns") == ["admission_exam_id"] and fk.get("referred_table") == "exams" and fk.get("name"):
            op.drop_constraint(fk["name"], "trainings", type_="foreignkey")
    inspector = inspect(bind)
    if not _has_fk(inspector, "trainings", ["admission_exam_id"]):
        op.create_foreign_key("fk_trainings_admission_exam_id", "trainings", "admission_exams", ["admission_exam_id"], ["id"])

    inspector = inspect(bind)
    if inspector.has_table("training_courses"):
        training_course_columns = {column["name"] for column in inspector.get_columns("training_courses")}
        if "primary_instructor_id" not in training_course_columns:
            op.add_column("training_courses", sa.Column("primary_instructor_id", sa.Integer(), nullable=True, comment="主讲教官ID"))
        if "assistant_instructor_ids" not in training_course_columns:
            op.add_column("training_courses", sa.Column("assistant_instructor_ids", sa.JSON(), nullable=True, comment="带教教官ID列表"))
    inspector = inspect(bind)
    if inspector.has_table("training_courses") and not _has_fk(inspector, "training_courses", ["primary_instructor_id"]):
        op.create_foreign_key("fk_training_courses_primary_instructor_id", "training_courses", "users", ["primary_instructor_id"], ["id"])

    inspector = inspect(bind)
    enrollment_columns = {column["name"] for column in inspector.get_columns("enrollments")} if inspector.has_table("enrollments") else set()
    for name, column in (
        ("contact_phone", sa.Column("contact_phone", sa.String(length=20), nullable=True, comment="联系电话")),
        ("need_accommodation", sa.Column("need_accommodation", sa.Boolean(), nullable=True, server_default=sa.false(), comment="是否需要住宿")),
        ("group_name", sa.Column("group_name", sa.String(length=100), nullable=True, comment="编组名称")),
        ("cadre_role", sa.Column("cadre_role", sa.String(length=100), nullable=True, comment="班干部角色")),
        ("profile_snapshot", sa.Column("profile_snapshot", sa.JSON(), nullable=True, comment="报名档案快照")),
        ("approved_at", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True, comment="通过时间")),
        ("reviewed_at", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间")),
        ("reviewed_by", sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人ID")),
        ("archived_at", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True, comment="归档时间")),
    ):
        if name not in enrollment_columns:
            op.add_column("enrollments", column)

    inspector = inspect(bind)
    if not _has_fk(inspector, "enrollments", ["reviewed_by"]):
        op.create_foreign_key("fk_enrollments_reviewed_by", "enrollments", "users", ["reviewed_by"], ["id"])

    inspector = inspect(bind)
    checkin_columns = {column["name"] for column in inspector.get_columns("checkin_records")} if inspector.has_table("checkin_records") else set()
    for name, column in (
        ("checkin_method", sa.Column("checkin_method", sa.String(length=20), nullable=True, comment="签到方式")),
        ("checkout_time", sa.Column("checkout_time", sa.String(length=10), nullable=True, comment="签退时间")),
        ("checkout_status", sa.Column("checkout_status", sa.String(length=20), nullable=True, server_default=sa.text("'pending'"), comment="签退状态")),
        ("checkout_method", sa.Column("checkout_method", sa.String(length=20), nullable=True, comment="签退方式")),
        ("evaluation_score", sa.Column("evaluation_score", sa.Integer(), nullable=True, comment="评课分数")),
        ("evaluation_comment", sa.Column("evaluation_comment", sa.Text(), nullable=True, comment="评课意见")),
        ("evaluation_submitted_at", sa.Column("evaluation_submitted_at", sa.DateTime(timezone=True), nullable=True, comment="评课时间")),
        ("absence_reason", sa.Column("absence_reason", sa.Text(), nullable=True, comment="缺勤原因")),
    ):
        if name not in checkin_columns:
            op.add_column("checkin_records", column)

    inspector = inspect(bind)
    if not inspector.has_table("training_histories"):
        op.create_table(
            "training_histories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("training_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("training_name", sa.String(length=200), nullable=False),
            sa.Column("training_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("attendance_rate", sa.Float(), nullable=True, server_default=sa.text("0")),
            sa.Column("completed_sessions", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("total_sessions", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("evaluation_score", sa.Float(), nullable=True, server_default=sa.text("0")),
            sa.Column("passed_exam_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("summary", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["training_id"], ["trainings.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("training_id", "user_id", name="uq_training_history_training_user"),
        )

    exams_table = sa.table(
        "exams",
        sa.column("id", sa.Integer()),
        sa.column("paper_id", sa.Integer()),
        sa.column("title", sa.String(length=200)),
        sa.column("description", sa.Text()),
        sa.column("duration", sa.Integer()),
        sa.column("total_score", sa.Integer()),
        sa.column("passing_score", sa.Integer()),
        sa.column("status", sa.String(length=50)),
        sa.column("type", sa.String(length=50)),
        sa.column("scope", sa.String(length=200)),
        sa.column("purpose", sa.String(length=50)),
        sa.column("max_attempts", sa.Integer()),
        sa.column("start_time", sa.DateTime(timezone=True)),
        sa.column("end_time", sa.DateTime(timezone=True)),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_by", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    admission_exams_table = sa.table(
        "admission_exams",
        sa.column("id", sa.Integer()),
        sa.column("paper_id", sa.Integer()),
        sa.column("title", sa.String(length=200)),
        sa.column("description", sa.Text()),
        sa.column("duration", sa.Integer()),
        sa.column("total_score", sa.Integer()),
        sa.column("passing_score", sa.Integer()),
        sa.column("status", sa.String(length=50)),
        sa.column("type", sa.String(length=50)),
        sa.column("scope", sa.String(length=200)),
        sa.column("max_attempts", sa.Integer()),
        sa.column("start_time", sa.DateTime(timezone=True)),
        sa.column("end_time", sa.DateTime(timezone=True)),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_by", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    exam_papers_table = sa.table(
        "exam_papers",
        sa.column("id", sa.Integer()),
        sa.column("title", sa.String(length=200)),
        sa.column("description", sa.Text()),
        sa.column("duration", sa.Integer()),
        sa.column("total_score", sa.Integer()),
        sa.column("passing_score", sa.Integer()),
        sa.column("type", sa.String(length=50)),
        sa.column("created_by", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    exam_questions_table = sa.table(
        "exam_questions",
        sa.column("exam_id", sa.Integer()),
        sa.column("question_id", sa.Integer()),
        sa.column("question_type", sa.String(length=20)),
        sa.column("content", sa.Text()),
        sa.column("options", sa.JSON()),
        sa.column("answer", sa.JSON()),
        sa.column("explanation", sa.Text()),
        sa.column("score", sa.Integer()),
        sa.column("knowledge_point", sa.String(length=200)),
    )
    exam_paper_questions_table = sa.table(
        "exam_paper_questions",
        sa.column("paper_id", sa.Integer()),
        sa.column("question_id", sa.Integer()),
        sa.column("sort_order", sa.Integer()),
        sa.column("question_type", sa.String(length=20)),
        sa.column("content", sa.Text()),
        sa.column("options", sa.JSON()),
        sa.column("answer", sa.JSON()),
        sa.column("explanation", sa.Text()),
        sa.column("score", sa.Integer()),
        sa.column("knowledge_point", sa.String(length=200)),
    )
    questions_table = sa.table(
        "questions",
        sa.column("id", sa.Integer()),
        sa.column("type", sa.String(length=20)),
        sa.column("content", sa.Text()),
        sa.column("options", sa.JSON()),
        sa.column("answer", sa.JSON()),
        sa.column("explanation", sa.Text()),
        sa.column("score", sa.Integer()),
        sa.column("knowledge_point", sa.String(length=200)),
    )
    exam_records_table = sa.table(
        "exam_records",
        sa.column("id", sa.Integer()),
        sa.column("exam_id", sa.Integer()),
        sa.column("user_id", sa.Integer()),
        sa.column("paper_id", sa.Integer()),
        sa.column("attempt_no", sa.Integer()),
        sa.column("status", sa.String(length=20)),
        sa.column("score", sa.Integer()),
        sa.column("result", sa.String(length=20)),
        sa.column("grade", sa.String(length=5)),
        sa.column("start_time", sa.DateTime(timezone=True)),
        sa.column("end_time", sa.DateTime(timezone=True)),
        sa.column("duration", sa.Integer()),
        sa.column("answers", sa.JSON()),
        sa.column("correct_count", sa.Integer()),
        sa.column("wrong_count", sa.Integer()),
        sa.column("wrong_questions", sa.JSON()),
        sa.column("wrong_question_details", sa.JSON()),
        sa.column("dimension_scores", sa.JSON()),
        sa.column("submitted_at", sa.DateTime(timezone=True)),
    )
    admission_exam_records_table = sa.table(
        "admission_exam_records",
        sa.column("id", sa.Integer()),
        sa.column("admission_exam_id", sa.Integer()),
        sa.column("paper_id", sa.Integer()),
        sa.column("user_id", sa.Integer()),
        sa.column("attempt_no", sa.Integer()),
        sa.column("status", sa.String(length=20)),
        sa.column("score", sa.Integer()),
        sa.column("result", sa.String(length=20)),
        sa.column("grade", sa.String(length=5)),
        sa.column("start_time", sa.DateTime(timezone=True)),
        sa.column("end_time", sa.DateTime(timezone=True)),
        sa.column("duration", sa.Integer()),
        sa.column("answers", sa.JSON()),
        sa.column("correct_count", sa.Integer()),
        sa.column("wrong_count", sa.Integer()),
        sa.column("wrong_questions", sa.JSON()),
        sa.column("wrong_question_details", sa.JSON()),
        sa.column("dimension_scores", sa.JSON()),
        sa.column("submitted_at", sa.DateTime(timezone=True)),
    )
    training_courses_table = sa.table(
        "training_courses",
        sa.column("id", sa.Integer()),
        sa.column("instructor", sa.String(length=100)),
        sa.column("primary_instructor_id", sa.Integer()),
    )
    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("username", sa.String(length=50)),
        sa.column("nickname", sa.String(length=100)),
    )
    trainings_table = sa.table(
        "trainings",
        sa.column("id", sa.Integer()),
        sa.column("status", sa.String(length=50)),
        sa.column("publish_status", sa.String(length=20)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )
    enrollments_table = sa.table(
        "enrollments",
        sa.column("id", sa.Integer()),
        sa.column("status", sa.String(length=50)),
        sa.column("enroll_time", sa.DateTime(timezone=True)),
        sa.column("approved_at", sa.DateTime(timezone=True)),
        sa.column("reviewed_at", sa.DateTime(timezone=True)),
    )

    question_rows = {
        row.id: row
        for row in bind.execute(
            sa.select(
                questions_table.c.id,
                questions_table.c.type,
                questions_table.c.content,
                questions_table.c.options,
                questions_table.c.answer,
                questions_table.c.explanation,
                questions_table.c.score,
                questions_table.c.knowledge_point,
            )
        ).all()
    }

    exam_rows = bind.execute(
        sa.select(
            exams_table.c.id,
            exams_table.c.paper_id,
            exams_table.c.title,
            exams_table.c.description,
            exams_table.c.duration,
            exams_table.c.total_score,
            exams_table.c.passing_score,
            exams_table.c.status,
            exams_table.c.type,
            exams_table.c.scope,
            exams_table.c.purpose,
            exams_table.c.max_attempts,
            exams_table.c.start_time,
            exams_table.c.end_time,
            exams_table.c.published_at,
            exams_table.c.created_by,
            exams_table.c.created_at,
            exams_table.c.updated_at,
        )
    ).all()

    for exam_row in exam_rows:
        paper_id = exam_row.paper_id
        if not paper_id:
            result = bind.execute(
                sa.insert(exam_papers_table).values(
                    title=exam_row.title,
                    description=exam_row.description,
                    duration=exam_row.duration or 60,
                    total_score=exam_row.total_score or 100,
                    passing_score=exam_row.passing_score or 60,
                    type=exam_row.type or "formal",
                    created_by=exam_row.created_by,
                    created_at=exam_row.created_at,
                )
            )
            paper_id = result.inserted_primary_key[0]
            bind.execute(
                sa.update(exams_table)
                .where(exams_table.c.id == exam_row.id)
                .values(
                    paper_id=paper_id,
                    purpose="class_assessment",
                    max_attempts=1,
                    allow_makeup=False,
                )
            )

        session_questions = bind.execute(
            sa.select(
                exam_questions_table.c.exam_id,
                exam_questions_table.c.question_id,
            ).where(exam_questions_table.c.exam_id == exam_row.id)
        ).all()
        for sort_order, session_question in enumerate(session_questions):
            question_row = question_rows.get(session_question.question_id)
            bind.execute(
                sa.insert(exam_paper_questions_table).values(
                    paper_id=paper_id,
                    question_id=session_question.question_id,
                    sort_order=sort_order,
                    question_type=question_row.type if question_row else "single",
                    content=question_row.content if question_row else f"历史题目#{session_question.question_id}",
                    options=question_row.options if question_row else [],
                    answer=question_row.answer if question_row else "A",
                    explanation=question_row.explanation if question_row else None,
                    score=question_row.score if question_row else 1,
                    knowledge_point=question_row.knowledge_point if question_row else None,
                )
            )
            bind.execute(
                sa.update(exam_questions_table)
                .where(
                    sa.and_(
                        exam_questions_table.c.exam_id == session_question.exam_id,
                        exam_questions_table.c.question_id == session_question.question_id,
                    )
                )
                .values(
                    question_type=question_row.type if question_row else "single",
                    content=question_row.content if question_row else f"历史题目#{session_question.question_id}",
                    options=question_row.options if question_row else [],
                    answer=question_row.answer if question_row else "A",
                    explanation=question_row.explanation if question_row else None,
                    score=question_row.score if question_row else 1,
                    knowledge_point=question_row.knowledge_point if question_row else None,
                )
            )

    admission_exam_ids = [
        row.id
        for row in exam_rows
        if (row.purpose or "class_assessment") == "admission"
    ]
    existing_admission_ids = {
        row.id
        for row in bind.execute(sa.select(admission_exams_table.c.id)).all()
    }
    for row in exam_rows:
        if row.id not in admission_exam_ids or row.id in existing_admission_ids:
            continue
        bind.execute(
            sa.insert(admission_exams_table).values(
                id=row.id,
                paper_id=row.paper_id,
                title=row.title,
                description=row.description,
                duration=row.duration or 60,
                total_score=row.total_score or 100,
                passing_score=row.passing_score or 60,
                status=row.status or "upcoming",
                type=row.type or "formal",
                scope=row.scope,
                max_attempts=row.max_attempts or 1,
                start_time=row.start_time,
                end_time=row.end_time,
                published_at=row.published_at,
                created_by=row.created_by,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )

    record_rows = bind.execute(
        sa.select(
            exam_records_table.c.id,
            exam_records_table.c.exam_id,
            exam_records_table.c.user_id,
            exams_table.c.paper_id,
            exam_records_table.c.end_time,
        ).select_from(
            exam_records_table.join(exams_table, exams_table.c.id == exam_records_table.c.exam_id)
        ).order_by(
            exam_records_table.c.user_id.asc(),
            exam_records_table.c.exam_id.asc(),
            exam_records_table.c.end_time.asc().nulls_last(),
            exam_records_table.c.id.asc(),
        )
    ).all()

    attempt_counter: dict[tuple[int, int], int] = {}
    for row in record_rows:
        key = (row.user_id, row.exam_id)
        attempt_counter[key] = attempt_counter.get(key, 0) + 1
        bind.execute(
            sa.update(exam_records_table)
            .where(exam_records_table.c.id == row.id)
            .values(
                paper_id=row.paper_id,
                attempt_no=attempt_counter[key],
                status="submitted",
                submitted_at=row.end_time,
            )
        )

    existing_admission_record_ids = {
        row.id
        for row in bind.execute(sa.select(admission_exam_records_table.c.id)).all()
    }
    admission_record_rows = bind.execute(
        sa.select(
            exam_records_table.c.id,
            exam_records_table.c.exam_id,
            exam_records_table.c.paper_id,
            exam_records_table.c.user_id,
            exam_records_table.c.attempt_no,
            exam_records_table.c.status,
            exam_records_table.c.score,
            exam_records_table.c.result,
            exam_records_table.c.grade,
            exam_records_table.c.start_time,
            exam_records_table.c.end_time,
            exam_records_table.c.duration,
            exam_records_table.c.answers,
            exam_records_table.c.correct_count,
            exam_records_table.c.wrong_count,
            exam_records_table.c.wrong_questions,
            exam_records_table.c.wrong_question_details,
            exam_records_table.c.dimension_scores,
            exam_records_table.c.submitted_at,
        ).where(exam_records_table.c.exam_id.in_(admission_exam_ids))
    ).all() if admission_exam_ids else []
    for row in admission_record_rows:
        if row.id in existing_admission_record_ids:
            continue
        bind.execute(
            sa.insert(admission_exam_records_table).values(
                id=row.id,
                admission_exam_id=row.exam_id,
                paper_id=row.paper_id,
                user_id=row.user_id,
                attempt_no=row.attempt_no or 1,
                status=row.status or "submitted",
                score=row.score or 0,
                result=row.result,
                grade=row.grade,
                start_time=row.start_time,
                end_time=row.end_time,
                duration=row.duration or 0,
                answers=row.answers,
                correct_count=row.correct_count or 0,
                wrong_count=row.wrong_count or 0,
                wrong_questions=row.wrong_questions,
                wrong_question_details=row.wrong_question_details,
                dimension_scores=row.dimension_scores,
                submitted_at=row.submitted_at,
            )
        )

    user_rows = bind.execute(
        sa.select(users_table.c.id, users_table.c.username, users_table.c.nickname)
    ).all() if inspector.has_table("users") else []
    user_name_map = {}
    for row in user_rows:
        if row.nickname:
            user_name_map[row.nickname] = row.id
        if row.username:
            user_name_map[row.username] = row.id
    course_rows = bind.execute(
        sa.select(training_courses_table.c.id, training_courses_table.c.instructor, training_courses_table.c.primary_instructor_id)
    ).all() if inspector.has_table("training_courses") else []
    for row in course_rows:
        if row.primary_instructor_id or not row.instructor:
            continue
        matched_id = user_name_map.get(row.instructor)
        if matched_id:
            bind.execute(
                sa.update(training_courses_table)
                .where(training_courses_table.c.id == row.id)
                .values(primary_instructor_id=matched_id)
            )

    if admission_exam_ids:
        bind.execute(
            sa.delete(exam_records_table).where(exam_records_table.c.exam_id.in_(admission_exam_ids))
        )
        bind.execute(
            sa.delete(exams_table).where(exams_table.c.id.in_(admission_exam_ids))
        )

    bind.execute(
        sa.update(trainings_table)
        .where(
            sa.or_(
                trainings_table.c.publish_status.is_(None),
                trainings_table.c.publish_status == "",
            )
        )
        .values(
            publish_status="published",
            published_at=sa.func.coalesce(trainings_table.c.published_at, trainings_table.c.created_at),
        )
    )

    bind.execute(
        sa.update(enrollments_table)
        .where(enrollments_table.c.status == "approved")
        .values(
            approved_at=sa.func.coalesce(enrollments_table.c.approved_at, enrollments_table.c.enroll_time),
            reviewed_at=sa.func.coalesce(enrollments_table.c.reviewed_at, enrollments_table.c.enroll_time),
        )
    )
    bind.execute(
        sa.update(enrollments_table)
        .where(enrollments_table.c.status == "rejected")
        .values(
            reviewed_at=sa.func.coalesce(enrollments_table.c.reviewed_at, enrollments_table.c.enroll_time),
        )
    )

    op.alter_column("exams", "purpose", existing_type=sa.String(length=50), nullable=False, server_default=sa.text("'class_assessment'"))
    op.alter_column("exams", "max_attempts", existing_type=sa.Integer(), nullable=False, server_default=sa.text("1"))
    op.alter_column("exams", "allow_makeup", existing_type=sa.Boolean(), nullable=False, server_default=sa.false())
    op.alter_column("exam_records", "attempt_no", existing_type=sa.Integer(), nullable=False, server_default=sa.text("1"))
    op.alter_column("exam_records", "status", existing_type=sa.String(length=20), nullable=False, server_default=sa.text("'submitted'"))
    op.alter_column("trainings", "publish_status", existing_type=sa.String(length=20), nullable=False, server_default=sa.text("'draft'"))
    op.alter_column("enrollments", "need_accommodation", existing_type=sa.Boolean(), nullable=False, server_default=sa.false())
    op.alter_column("checkin_records", "checkout_status", existing_type=sa.String(length=20), nullable=False, server_default=sa.text("'pending'"))
    op.alter_column("exam_questions", "question_type", existing_type=sa.String(length=20), nullable=False)
    op.alter_column("exam_questions", "content", existing_type=sa.Text(), nullable=False)
    op.alter_column("exam_questions", "answer", existing_type=sa.JSON(), nullable=False)
    op.alter_column("exam_questions", "score", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("training_histories"):
        op.drop_table("training_histories")

    inspector = inspect(bind)
    if inspector.has_table("training_courses"):
        if any(fk.get("name") == "fk_training_courses_primary_instructor_id" for fk in inspector.get_foreign_keys("training_courses")):
            op.drop_constraint("fk_training_courses_primary_instructor_id", "training_courses", type_="foreignkey")
        for column_name in ("assistant_instructor_ids", "primary_instructor_id"):
            if _has_column(inspector, "training_courses", column_name):
                op.drop_column("training_courses", column_name)

    for index_name in ("ix_exam_records_paper_id",):
        if _has_index(inspector, "exam_records", index_name):
            op.drop_index(index_name, table_name="exam_records")
    if _has_fk(inspector, "exam_records", ["paper_id"]):
        op.drop_constraint("fk_exam_records_paper_id", "exam_records", type_="foreignkey")
    for column_name in ("submitted_at", "wrong_question_details", "status", "attempt_no", "paper_id"):
        if _has_column(inspector, "exam_records", column_name):
            op.drop_column("exam_records", column_name)

    inspector = inspect(bind)
    for fk_name, table_name in (
        ("fk_trainings_admission_exam_id", "trainings"),
        ("fk_trainings_locked_by", "trainings"),
        ("fk_trainings_published_by", "trainings"),
    ):
        if any(fk.get("name") == fk_name for fk in inspector.get_foreign_keys(table_name)):
            op.drop_constraint(fk_name, table_name, type_="foreignkey")
    for column_name in (
        "locked_at", "published_at", "enrollment_end_at", "enrollment_start_at",
        "admission_exam_id", "locked_by", "published_by", "class_code", "publish_status",
    ):
        if _has_column(inspector, "trainings", column_name):
            op.drop_column("trainings", column_name)

    inspector = inspect(bind)
    if inspector.has_table("admission_exam_records"):
        op.drop_table("admission_exam_records")
    if inspector.has_table("admission_exams"):
        op.drop_table("admission_exams")

    inspector = inspect(bind)
    if any(fk.get("name") == "fk_enrollments_reviewed_by" for fk in inspector.get_foreign_keys("enrollments")):
        op.drop_constraint("fk_enrollments_reviewed_by", "enrollments", type_="foreignkey")
    for column_name in (
        "archived_at", "reviewed_by", "reviewed_at", "approved_at",
        "profile_snapshot", "cadre_role", "group_name", "need_accommodation", "contact_phone",
    ):
        if _has_column(inspector, "enrollments", column_name):
            op.drop_column("enrollments", column_name)

    inspector = inspect(bind)
    for column_name in (
        "absence_reason", "evaluation_submitted_at", "evaluation_comment", "evaluation_score",
        "checkout_method", "checkout_status", "checkout_time", "checkin_method",
    ):
        if _has_column(inspector, "checkin_records", column_name):
            op.drop_column("checkin_records", column_name)

    inspector = inspect(bind)
    for column_name in ("knowledge_point", "score", "explanation", "answer", "options", "content", "question_type"):
        if _has_column(inspector, "exam_questions", column_name):
            op.drop_column("exam_questions", column_name)

    inspector = inspect(bind)
    for index_name in ("ix_exams_training_id", "ix_exams_paper_id"):
        if _has_index(inspector, "exams", index_name):
            op.drop_index(index_name, table_name="exams")
    for fk_name, table_name in (
        ("fk_exams_training_id", "exams"),
        ("fk_exams_paper_id", "exams"),
    ):
        if any(fk.get("name") == fk_name for fk in inspector.get_foreign_keys(table_name)):
            op.drop_constraint(fk_name, table_name, type_="foreignkey")
    for column_name in ("published_at", "allow_makeup", "max_attempts", "training_id", "purpose", "paper_id"):
        if _has_column(inspector, "exams", column_name):
            op.drop_column("exams", column_name)

    if inspector.has_table("exam_paper_questions"):
        op.drop_table("exam_paper_questions")
    if inspector.has_table("exam_papers"):
        op.drop_table("exam_papers")
