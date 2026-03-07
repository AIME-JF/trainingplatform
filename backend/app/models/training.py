"""
培训管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Float, JSON, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Training(Base):
    """培训班表"""
    __tablename__ = 'trainings'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment='培训名称')
    type = Column(String(50), nullable=False, comment='培训类型: basic/special/promotion/online')
    status = Column(String(50), default='upcoming', comment='状态: active/upcoming/ended')
    start_date = Column(Date, nullable=True, comment='开始日期')
    end_date = Column(Date, nullable=True, comment='结束日期')
    location = Column(String(200), nullable=True, comment='培训地点')
    instructor_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='负责教官ID')
    capacity = Column(Integer, default=0, comment='容量')
    description = Column(Text, comment='培训描述')
    subjects = Column(JSON, nullable=True, comment='科目标签')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    instructor = relationship("User", foreign_keys=[instructor_id])
    courses = relationship("TrainingCourse", back_populates="training", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="training", cascade="all, delete-orphan")
    schedule_items = relationship("ScheduleItem", back_populates="training", cascade="all, delete-orphan")


class TrainingCourse(Base):
    """培训班课程安排表"""
    __tablename__ = 'training_courses'

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=False, comment='培训班ID')
    name = Column(String(200), nullable=False, comment='课程名称')
    instructor = Column(String(100), nullable=True, comment='授课教官')
    hours = Column(Float, default=0, comment='课时')
    type = Column(String(50), default='theory', comment='类型: theory/practice')
    schedules = Column(JSON, nullable=True, comment='排课清单')

    # 关联关系
    training = relationship("Training", back_populates="courses")


class Enrollment(Base):
    """培训报名表"""
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=False, comment='培训班ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    status = Column(String(50), default='pending', comment='状态: pending/approved/rejected')
    note = Column(Text, nullable=True, comment='备注/拒绝原因')
    enroll_time = Column(DateTime(timezone=True), server_default=func.now(), comment='报名时间')

    __table_args__ = (
        UniqueConstraint('training_id', 'user_id', name='uq_enrollment_training_user'),
    )

    # 关联关系
    training = relationship("Training", back_populates="enrollments")
    user = relationship("User", foreign_keys=[user_id])


class CheckinRecord(Base):
    """签到记录表"""
    __tablename__ = 'checkin_records'

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=False, comment='培训班ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    date = Column(Date, nullable=False, comment='签到日期')
    time = Column(String(10), nullable=True, comment='签到时间 HH:MM')
    status = Column(String(20), default='on_time', comment='状态: on_time/late/absent')
    session_key = Column(String(100), nullable=False, default='start', comment='签到场次标识')

    __table_args__ = (
        UniqueConstraint('training_id', 'user_id', 'date', 'session_key', name='uq_checkin_training_user_date_session'),
        Index('ix_checkin_training_date_session', 'training_id', 'date', 'session_key'),
    )

    # 关联关系
    training = relationship("Training", foreign_keys=[training_id])
    user = relationship("User", foreign_keys=[user_id])


class ScheduleItem(Base):
    """训练计划条目表"""
    __tablename__ = 'schedule_items'

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=False, comment='培训班ID')
    week_start = Column(Date, nullable=True, comment='周起始日')
    day = Column(Integer, nullable=True, comment='星期1-5')
    date = Column(Date, nullable=True, comment='日期')
    time_start = Column(String(10), nullable=True, comment='开始时间 HH:MM')
    time_end = Column(String(10), nullable=True, comment='结束时间 HH:MM')
    title = Column(String(200), nullable=False, comment='标题')
    type = Column(String(50), default='theory', comment='类型: theory/skill/review/physical/drill')
    location = Column(String(200), nullable=True, comment='地点')
    instructor = Column(String(100), nullable=True, comment='教官')
    participants = Column(String(200), nullable=True, comment='参与人员')
    content = Column(Text, nullable=True, comment='内容')
    status = Column(String(50), default='pending', comment='状态: completed/in_progress/pending')

    # 关联关系
    training = relationship("Training", back_populates="schedule_items")
