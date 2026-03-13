"""repair_stamped_p0_schema

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-13 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
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


def _has_fk(inspector, table_name: str, constrained_columns: list[str], referred_table: str | None = None) -> bool:
    if not inspector.has_table(table_name):
        return False
    for fk in inspector.get_foreign_keys(table_name):
        if fk.get("constrained_columns") != constrained_columns:
            continue
        if referred_table and fk.get("referred_table") != referred_table:
            continue
        return True
    return False


def _ensure_columns(table_name: str, columns: list[tuple[str, sa.Column]]) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    for name, column in columns:
        if name not in existing_columns:
            op.add_column(table_name, column)


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
    else:
        _ensure_columns(
            "exam_papers",
            [
                ("description", sa.Column("description", sa.Text(), nullable=True, comment="试卷描述")),
                ("duration", sa.Column("duration", sa.Integer(), nullable=True, server_default=sa.text("60"), comment="考试时长(分钟)")),
                ("total_score", sa.Column("total_score", sa.Integer(), nullable=True, server_default=sa.text("100"), comment="总分")),
                ("passing_score", sa.Column("passing_score", sa.Integer(), nullable=True, server_default=sa.text("60"), comment="及格分")),
                ("type", sa.Column("type", sa.String(length=50), nullable=True, server_default=sa.text("'formal'"), comment="试卷类型")),
                ("created_by", sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID")),
                ("created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"))),
                ("updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)),
            ],
        )
        inspector = inspect(bind)
        if not _has_fk(inspector, "exam_papers", ["created_by"], "users"):
            op.create_foreign_key("fk_exam_papers_created_by", "exam_papers", "users", ["created_by"], ["id"])

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
        _ensure_columns(
            "exam_paper_questions",
            [
                ("sort_order", sa.Column("sort_order", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("question_type", sa.Column("question_type", sa.String(length=20), nullable=True, comment="题目类型快照")),
                ("content", sa.Column("content", sa.Text(), nullable=True, comment="题干快照")),
                ("options", sa.Column("options", sa.JSON(), nullable=True, comment="选项快照")),
                ("answer", sa.Column("answer", sa.JSON(), nullable=True, comment="答案快照")),
                ("explanation", sa.Column("explanation", sa.Text(), nullable=True, comment="解析快照")),
                ("score", sa.Column("score", sa.Integer(), nullable=True, comment="分值快照")),
                ("knowledge_point", sa.Column("knowledge_point", sa.String(length=200), nullable=True, comment="知识点快照")),
            ],
        )
        inspector = inspect(bind)
        if not _has_fk(inspector, "exam_paper_questions", ["paper_id"], "exam_papers"):
            op.create_foreign_key(
                "fk_exam_paper_questions_paper_id",
                "exam_paper_questions",
                "exam_papers",
                ["paper_id"],
                ["id"],
                ondelete="CASCADE",
            )
        if not _has_fk(inspector, "exam_paper_questions", ["question_id"], "questions"):
            op.create_foreign_key(
                "fk_exam_paper_questions_question_id",
                "exam_paper_questions",
                "questions",
                ["question_id"],
                ["id"],
                ondelete="CASCADE",
            )

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
    else:
        _ensure_columns(
            "admission_exams",
            [
                ("paper_id", sa.Column("paper_id", sa.Integer(), nullable=True)),
                ("description", sa.Column("description", sa.Text(), nullable=True)),
                ("duration", sa.Column("duration", sa.Integer(), nullable=True, server_default=sa.text("60"))),
                ("total_score", sa.Column("total_score", sa.Integer(), nullable=True, server_default=sa.text("100"))),
                ("passing_score", sa.Column("passing_score", sa.Integer(), nullable=True, server_default=sa.text("60"))),
                ("status", sa.Column("status", sa.String(length=50), nullable=True, server_default=sa.text("'upcoming'"))),
                ("type", sa.Column("type", sa.String(length=50), nullable=True, server_default=sa.text("'formal'"))),
                ("scope", sa.Column("scope", sa.String(length=200), nullable=True)),
                ("max_attempts", sa.Column("max_attempts", sa.Integer(), nullable=True, server_default=sa.text("1"))),
                ("start_time", sa.Column("start_time", sa.DateTime(timezone=True), nullable=True)),
                ("end_time", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True)),
                ("published_at", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True)),
                ("created_by", sa.Column("created_by", sa.Integer(), nullable=True)),
                ("created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"))),
                ("updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)),
            ],
        )
        inspector = inspect(bind)
        if not _has_fk(inspector, "admission_exams", ["paper_id"], "exam_papers"):
            op.create_foreign_key("fk_admission_exams_paper_id", "admission_exams", "exam_papers", ["paper_id"], ["id"])
        if not _has_fk(inspector, "admission_exams", ["created_by"], "users"):
            op.create_foreign_key("fk_admission_exams_created_by", "admission_exams", "users", ["created_by"], ["id"])

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
    else:
        _ensure_columns(
            "admission_exam_records",
            [
                ("paper_id", sa.Column("paper_id", sa.Integer(), nullable=True)),
                ("attempt_no", sa.Column("attempt_no", sa.Integer(), nullable=True, server_default=sa.text("1"))),
                ("status", sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'submitted'"))),
                ("result", sa.Column("result", sa.String(length=20), nullable=True)),
                ("grade", sa.Column("grade", sa.String(length=5), nullable=True)),
                ("start_time", sa.Column("start_time", sa.DateTime(timezone=True), nullable=True)),
                ("end_time", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True)),
                ("duration", sa.Column("duration", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("answers", sa.Column("answers", sa.JSON(), nullable=True)),
                ("correct_count", sa.Column("correct_count", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("wrong_count", sa.Column("wrong_count", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("wrong_questions", sa.Column("wrong_questions", sa.JSON(), nullable=True)),
                ("wrong_question_details", sa.Column("wrong_question_details", sa.JSON(), nullable=True)),
                ("dimension_scores", sa.Column("dimension_scores", sa.JSON(), nullable=True)),
                ("submitted_at", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"))),
            ],
        )
        inspector = inspect(bind)
        if not _has_fk(inspector, "admission_exam_records", ["admission_exam_id"], "admission_exams"):
            op.create_foreign_key(
                "fk_admission_exam_records_exam_id",
                "admission_exam_records",
                "admission_exams",
                ["admission_exam_id"],
                ["id"],
            )
        if not _has_fk(inspector, "admission_exam_records", ["paper_id"], "exam_papers"):
            op.create_foreign_key(
                "fk_admission_exam_records_paper_id",
                "admission_exam_records",
                "exam_papers",
                ["paper_id"],
                ["id"],
            )
        if not _has_fk(inspector, "admission_exam_records", ["user_id"], "users"):
            op.create_foreign_key(
                "fk_admission_exam_records_user_id",
                "admission_exam_records",
                "users",
                ["user_id"],
                ["id"],
            )

    _ensure_columns(
        "exams",
        [
            ("paper_id", sa.Column("paper_id", sa.Integer(), nullable=True, comment="试卷ID")),
            ("purpose", sa.Column("purpose", sa.String(length=50), nullable=True, server_default=sa.text("'class_assessment'"), comment="用途")),
            ("training_id", sa.Column("training_id", sa.Integer(), nullable=True, comment="关联培训班ID")),
            ("max_attempts", sa.Column("max_attempts", sa.Integer(), nullable=True, server_default=sa.text("1"), comment="最大作答次数")),
            ("allow_makeup", sa.Column("allow_makeup", sa.Boolean(), nullable=True, server_default=sa.false(), comment="是否允许补考")),
            ("published_at", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间")),
        ],
    )
    inspector = inspect(bind)
    if not _has_fk(inspector, "exams", ["paper_id"], "exam_papers"):
        op.create_foreign_key("fk_exams_paper_id", "exams", "exam_papers", ["paper_id"], ["id"])
    if not _has_fk(inspector, "exams", ["training_id"], "trainings"):
        op.create_foreign_key("fk_exams_training_id", "exams", "trainings", ["training_id"], ["id"])
    if not _has_index(inspector, "exams", "ix_exams_paper_id"):
        op.create_index("ix_exams_paper_id", "exams", ["paper_id"], unique=False)
    if not _has_index(inspector, "exams", "ix_exams_training_id"):
        op.create_index("ix_exams_training_id", "exams", ["training_id"], unique=False)

    _ensure_columns(
        "exam_questions",
        [
            ("question_type", sa.Column("question_type", sa.String(length=20), nullable=True, comment="题目类型")),
            ("content", sa.Column("content", sa.Text(), nullable=True, comment="题干快照")),
            ("options", sa.Column("options", sa.JSON(), nullable=True, comment="选项快照")),
            ("answer", sa.Column("answer", sa.JSON(), nullable=True, comment="答案快照")),
            ("explanation", sa.Column("explanation", sa.Text(), nullable=True, comment="解析快照")),
            ("score", sa.Column("score", sa.Integer(), nullable=True, comment="分值快照")),
            ("knowledge_point", sa.Column("knowledge_point", sa.String(length=200), nullable=True, comment="知识点快照")),
        ],
    )

    _ensure_columns(
        "exam_records",
        [
            ("paper_id", sa.Column("paper_id", sa.Integer(), nullable=True, comment="试卷ID")),
            ("attempt_no", sa.Column("attempt_no", sa.Integer(), nullable=True, server_default=sa.text("1"), comment="第几次作答")),
            ("status", sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'submitted'"), comment="作答状态")),
            ("wrong_question_details", sa.Column("wrong_question_details", sa.JSON(), nullable=True, comment="错题详情快照")),
            ("submitted_at", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"), comment="提交时间")),
        ],
    )
    inspector = inspect(bind)
    if not _has_fk(inspector, "exam_records", ["paper_id"], "exam_papers"):
        op.create_foreign_key("fk_exam_records_paper_id", "exam_records", "exam_papers", ["paper_id"], ["id"])
    if not _has_index(inspector, "exam_records", "ix_exam_records_paper_id"):
        op.create_index("ix_exam_records_paper_id", "exam_records", ["paper_id"], unique=False)

    _ensure_columns(
        "trainings",
        [
            ("publish_status", sa.Column("publish_status", sa.String(length=20), nullable=True, server_default=sa.text("'draft'"), comment="发布状态")),
            ("class_code", sa.Column("class_code", sa.String(length=100), nullable=True, comment="班次编号")),
            ("published_by", sa.Column("published_by", sa.Integer(), nullable=True, comment="发布人ID")),
            ("locked_by", sa.Column("locked_by", sa.Integer(), nullable=True, comment="锁定人ID")),
            ("admission_exam_id", sa.Column("admission_exam_id", sa.Integer(), nullable=True, comment="准入考试ID")),
            ("enrollment_start_at", sa.Column("enrollment_start_at", sa.DateTime(timezone=True), nullable=True, comment="报名开始时间")),
            ("enrollment_end_at", sa.Column("enrollment_end_at", sa.DateTime(timezone=True), nullable=True, comment="报名截止时间")),
            ("published_at", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间")),
            ("locked_at", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True, comment="名单锁定时间")),
        ],
    )
    inspector = inspect(bind)
    if not _has_fk(inspector, "trainings", ["published_by"], "users"):
        op.create_foreign_key("fk_trainings_published_by", "trainings", "users", ["published_by"], ["id"])
    if not _has_fk(inspector, "trainings", ["locked_by"], "users"):
        op.create_foreign_key("fk_trainings_locked_by", "trainings", "users", ["locked_by"], ["id"])
    for fk in inspector.get_foreign_keys("trainings"):
        if (
            fk.get("constrained_columns") == ["admission_exam_id"]
            and fk.get("referred_table") == "exams"
            and fk.get("name")
        ):
            op.drop_constraint(fk["name"], "trainings", type_="foreignkey")
    inspector = inspect(bind)
    if not _has_fk(inspector, "trainings", ["admission_exam_id"], "admission_exams"):
        op.create_foreign_key(
            "fk_trainings_admission_exam_id",
            "trainings",
            "admission_exams",
            ["admission_exam_id"],
            ["id"],
        )

    _ensure_columns(
        "training_courses",
        [
            ("primary_instructor_id", sa.Column("primary_instructor_id", sa.Integer(), nullable=True, comment="主讲教官ID")),
            ("assistant_instructor_ids", sa.Column("assistant_instructor_ids", sa.JSON(), nullable=True, comment="带教教官ID列表")),
        ],
    )
    inspector = inspect(bind)
    if not _has_fk(inspector, "training_courses", ["primary_instructor_id"], "users"):
        op.create_foreign_key(
            "fk_training_courses_primary_instructor_id",
            "training_courses",
            "users",
            ["primary_instructor_id"],
            ["id"],
        )

    _ensure_columns(
        "enrollments",
        [
            ("contact_phone", sa.Column("contact_phone", sa.String(length=20), nullable=True, comment="联系电话")),
            ("need_accommodation", sa.Column("need_accommodation", sa.Boolean(), nullable=True, server_default=sa.false(), comment="是否需要住宿")),
            ("group_name", sa.Column("group_name", sa.String(length=100), nullable=True, comment="编组名称")),
            ("cadre_role", sa.Column("cadre_role", sa.String(length=100), nullable=True, comment="班干部角色")),
            ("profile_snapshot", sa.Column("profile_snapshot", sa.JSON(), nullable=True, comment="报名档案快照")),
            ("approved_at", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True, comment="通过时间")),
            ("reviewed_at", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间")),
            ("reviewed_by", sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人ID")),
            ("archived_at", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True, comment="归档时间")),
        ],
    )
    inspector = inspect(bind)
    if not _has_fk(inspector, "enrollments", ["reviewed_by"], "users"):
        op.create_foreign_key("fk_enrollments_reviewed_by", "enrollments", "users", ["reviewed_by"], ["id"])

    _ensure_columns(
        "checkin_records",
        [
            ("checkin_method", sa.Column("checkin_method", sa.String(length=20), nullable=True, comment="签到方式")),
            ("checkout_time", sa.Column("checkout_time", sa.String(length=10), nullable=True, comment="签退时间")),
            ("checkout_status", sa.Column("checkout_status", sa.String(length=20), nullable=True, server_default=sa.text("'pending'"), comment="签退状态")),
            ("checkout_method", sa.Column("checkout_method", sa.String(length=20), nullable=True, comment="签退方式")),
            ("evaluation_score", sa.Column("evaluation_score", sa.Integer(), nullable=True, comment="评课分数")),
            ("evaluation_comment", sa.Column("evaluation_comment", sa.Text(), nullable=True, comment="评课意见")),
            ("evaluation_submitted_at", sa.Column("evaluation_submitted_at", sa.DateTime(timezone=True), nullable=True, comment="评课时间")),
            ("absence_reason", sa.Column("absence_reason", sa.Text(), nullable=True, comment="缺勤原因")),
        ],
    )

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
    else:
        _ensure_columns(
            "training_histories",
            [
                ("start_date", sa.Column("start_date", sa.Date(), nullable=True)),
                ("end_date", sa.Column("end_date", sa.Date(), nullable=True)),
                ("attendance_rate", sa.Column("attendance_rate", sa.Float(), nullable=True, server_default=sa.text("0"))),
                ("completed_sessions", sa.Column("completed_sessions", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("total_sessions", sa.Column("total_sessions", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("evaluation_score", sa.Column("evaluation_score", sa.Float(), nullable=True, server_default=sa.text("0"))),
                ("passed_exam_count", sa.Column("passed_exam_count", sa.Integer(), nullable=True, server_default=sa.text("0"))),
                ("archived_at", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP"))),
                ("summary", sa.Column("summary", sa.JSON(), nullable=True)),
            ],
        )
        inspector = inspect(bind)
        if not _has_fk(inspector, "training_histories", ["training_id"], "trainings"):
            op.create_foreign_key(
                "fk_training_histories_training_id",
                "training_histories",
                "trainings",
                ["training_id"],
                ["id"],
                ondelete="CASCADE",
            )
        if not _has_fk(inspector, "training_histories", ["user_id"], "users"):
            op.create_foreign_key(
                "fk_training_histories_user_id",
                "training_histories",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )

    op.execute(sa.text("UPDATE exams SET purpose = 'class_assessment' WHERE purpose IS NULL"))
    op.execute(sa.text("UPDATE exam_records SET attempt_no = 1 WHERE attempt_no IS NULL"))
    op.execute(sa.text("UPDATE exam_records SET status = 'submitted' WHERE status IS NULL"))
    op.execute(sa.text("UPDATE enrollments SET need_accommodation = FALSE WHERE need_accommodation IS NULL"))
    op.execute(sa.text("UPDATE checkin_records SET checkout_status = 'pending' WHERE checkout_status IS NULL"))


def downgrade() -> None:
    # 这是兼容修复迁移，不提供破坏性回滚。
    pass
