"""
培训管理相关的数据库模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Training(Base):
    """培训班表"""

    __tablename__ = "trainings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="培训名称")
    type = Column(String(50), nullable=False, comment="培训类型: basic/special/promotion/online")
    status = Column(String(50), default="upcoming", comment="状态: active/upcoming/ended")
    publish_status = Column(String(20), default="draft", comment="发布状态: draft/published")
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    location = Column(String(200), nullable=True, comment="培训地点")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="归属部门ID")
    police_type_id = Column(Integer, ForeignKey("police_types.id"), nullable=True, comment="警种ID")
    training_base_id = Column(Integer, ForeignKey("training_bases.id"), nullable=True, comment="培训基地ID")
    class_code = Column(String(100), nullable=True, comment="班次编号")
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="班主任ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    published_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="发布人ID")
    locked_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="锁定人ID")
    admission_exam_id = Column(Integer, ForeignKey("admission_exams.id"), nullable=True, comment="准入考试ID")
    capacity = Column(Integer, default=0, comment="容量")
    description = Column(Text, comment="培训描述")
    subjects = Column(JSON, nullable=True, comment="科目标签")
    enrollment_requires_approval = Column(Boolean, default=True, nullable=False, comment="报名是否需要审核")
    enrollment_start_at = Column(DateTime(timezone=True), nullable=True, comment="报名开始时间")
    enrollment_end_at = Column(DateTime(timezone=True), nullable=True, comment="报名截止时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    locked_at = Column(DateTime(timezone=True), nullable=True, comment="名单锁定时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    instructor = relationship("User", foreign_keys=[instructor_id])
    creator = relationship("User", foreign_keys=[created_by])
    department = relationship("Department", foreign_keys=[department_id])
    police_type = relationship("PoliceType", foreign_keys=[police_type_id])
    training_base = relationship("TrainingBase", foreign_keys=[training_base_id], back_populates="linked_trainings")
    publisher = relationship("User", foreign_keys=[published_by])
    locker = relationship("User", foreign_keys=[locked_by])
    admission_exam = relationship("AdmissionExam", foreign_keys=[admission_exam_id], back_populates="linked_trainings")
    courses = relationship("TrainingCourse", back_populates="training", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="training", cascade="all, delete-orphan")
    schedule_items = relationship("ScheduleItem", back_populates="training", cascade="all, delete-orphan")
    exam_sessions = relationship("Exam", back_populates="training", foreign_keys="Exam.training_id")
    histories = relationship("TrainingHistory", back_populates="training", cascade="all, delete-orphan")
    course_change_logs = relationship("TrainingCourseChangeLog", back_populates="training", cascade="all, delete-orphan")


class TrainingBase(Base):
    """培训基地表"""

    __tablename__ = "training_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="培训基地名称")
    location = Column(String(200), nullable=False, comment="培训基地地点")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="关联部门ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    description = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    department = relationship("Department", foreign_keys=[department_id])
    creator = relationship("User", foreign_keys=[created_by])
    linked_trainings = relationship("Training", back_populates="training_base")


class TrainingCourse(Base):
    """培训班课程安排表"""

    __tablename__ = "training_courses"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, comment="培训班ID")
    course_key = Column(String(36), nullable=True, index=True, comment="稳定课程键")
    name = Column(String(200), nullable=False, comment="课程名称")
    instructor = Column(String(100), nullable=True, comment="主讲教官名称")
    primary_instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="主讲教官ID")
    assistant_instructor_ids = Column(JSON, nullable=True, comment="带教教官ID列表")
    hours = Column(Float, default=0, comment="课时")
    type = Column(String(50), default="theory", comment="类型: theory/practice")
    schedules = Column(JSON, nullable=True, comment="排课清单，包含课次状态与签到签退生命周期")

    __table_args__ = (
        UniqueConstraint("training_id", "course_key", name="uq_training_course_key"),
    )

    training = relationship("Training", back_populates="courses")
    primary_instructor = relationship("User", foreign_keys=[primary_instructor_id])


class Enrollment(Base):
    """培训报名表"""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, comment="培训班ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    status = Column(String(50), default="pending", comment="状态: pending/approved/rejected")
    note = Column(Text, nullable=True, comment="备注/拒绝原因")
    contact_phone = Column(String(20), nullable=True, comment="报名联系电话")
    need_accommodation = Column(Boolean, default=False, comment="是否需要住宿")
    group_name = Column(String(100), nullable=True, comment="编组名称")
    cadre_role = Column(String(100), nullable=True, comment="班干部角色")
    profile_snapshot = Column(JSON, nullable=True, comment="报名时档案快照")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="通过时间")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    archived_at = Column(DateTime(timezone=True), nullable=True, comment="归档时间")
    enroll_time = Column(DateTime(timezone=True), server_default=func.now(), comment="报名时间")

    __table_args__ = (
        UniqueConstraint("training_id", "user_id", name="uq_enrollment_training_user"),
    )

    training = relationship("Training", back_populates="enrollments")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class CheckinRecord(Base):
    """签到记录表"""

    __tablename__ = "checkin_records"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, comment="培训班ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    date = Column(Date, nullable=False, comment="签到日期")
    time = Column(String(10), nullable=True, comment="签到时间 HH:MM")
    status = Column(String(20), default="on_time", comment="状态: on_time/late/absent")
    session_key = Column(String(100), nullable=False, default="start", comment="课次标识")
    checkin_method = Column(String(20), nullable=True, comment="签到方式: qr/manual")
    checkout_time = Column(String(10), nullable=True, comment="签退时间 HH:MM")
    checkout_status = Column(String(20), default="pending", comment="签退状态: pending/completed")
    checkout_method = Column(String(20), nullable=True, comment="签退方式: qr/manual")
    evaluation_score = Column(Integer, nullable=True, comment="评课分数")
    evaluation_comment = Column(Text, nullable=True, comment="评课意见")
    evaluation_submitted_at = Column(DateTime(timezone=True), nullable=True, comment="评课提交时间")
    absence_reason = Column(Text, nullable=True, comment="缺勤原因/留痕")

    __table_args__ = (
        UniqueConstraint(
            "training_id",
            "user_id",
            "date",
            "session_key",
            name="uq_checkin_training_user_date_session",
        ),
        Index("ix_checkin_training_date_session", "training_id", "date", "session_key"),
    )

    training = relationship("Training", foreign_keys=[training_id])
    user = relationship("User", foreign_keys=[user_id])


class ScheduleItem(Base):
    """训练计划条目表"""

    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, comment="培训班ID")
    week_start = Column(Date, nullable=True, comment="周起始日")
    day = Column(Integer, nullable=True, comment="星期1-7")
    date = Column(Date, nullable=True, comment="日期")
    time_start = Column(String(10), nullable=True, comment="开始时间 HH:MM")
    time_end = Column(String(10), nullable=True, comment="结束时间 HH:MM")
    title = Column(String(200), nullable=False, comment="标题")
    type = Column(String(50), default="theory", comment="类型: theory/skill/review/physical/drill")
    location = Column(String(200), nullable=True, comment="地点")
    instructor = Column(String(100), nullable=True, comment="教官")
    participants = Column(String(200), nullable=True, comment="参与人员")
    content = Column(Text, nullable=True, comment="内容")
    status = Column(String(50), default="pending", comment="状态: completed/in_progress/pending")

    training = relationship("Training", back_populates="schedule_items")


class TrainingHistory(Base):
    """培训训历归档表"""

    __tablename__ = "training_histories"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, comment="培训班ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    training_name = Column(String(200), nullable=False, comment="培训名称快照")
    training_type = Column(String(50), nullable=False, comment="培训类型快照")
    status = Column(String(50), nullable=False, comment="培训状态快照")
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    attendance_rate = Column(Float, default=0, comment="出勤率")
    completed_sessions = Column(Integer, default=0, comment="完成课次")
    total_sessions = Column(Integer, default=0, comment="总课次")
    evaluation_score = Column(Float, default=0, comment="评课均分")
    passed_exam_count = Column(Integer, default=0, comment="通过考试场次数")
    archived_at = Column(DateTime(timezone=True), server_default=func.now(), comment="归档时间")
    summary = Column(JSON, nullable=True, comment="扩展摘要")

    __table_args__ = (
        UniqueConstraint("training_id", "user_id", name="uq_training_history_training_user"),
    )

    training = relationship("Training", back_populates="histories")
    user = relationship("User", foreign_keys=[user_id])


class TrainingCourseChangeLog(Base):
    """培训班课程/课次变更日志"""

    __tablename__ = "training_course_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True, comment="培训班ID")
    course_key = Column(String(36), nullable=True, index=True, comment="稳定课程键")
    session_key = Column(String(100), nullable=True, index=True, comment="课次键")
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="操作人ID，系统事件为空")
    target_type = Column(String(20), nullable=False, comment="对象类型: course/session")
    action = Column(String(30), nullable=False, comment="动作: create/update/delete/status_change")
    source = Column(String(50), nullable=False, comment="来源: detail_update/import_schedule/system_refresh 等")
    batch_id = Column(String(36), nullable=False, index=True, comment="同一次操作批次号")
    course_name = Column(String(200), nullable=True, comment="课程名快照")
    session_label = Column(String(200), nullable=True, comment="课次标签快照")
    summary = Column(String(500), nullable=True, comment="变更摘要")
    before_json = Column(JSON, nullable=True, comment="变更前快照")
    after_json = Column(JSON, nullable=True, comment="变更后快照")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    __table_args__ = (
        Index("ix_training_course_change_logs_training_created", "training_id", "created_at"),
    )

    training = relationship("Training", back_populates="course_change_logs")
    actor = relationship("User", foreign_keys=[actor_id])
