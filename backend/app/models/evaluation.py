"""
评价模块模型
"""
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


VALID_TARGET_TYPES = ("course", "instructor", "training", "training_base")


class EvaluationTemplate(Base):
    """评价问卷模板（固定 4 种，每种 target_type 唯一）"""

    __tablename__ = "evaluation_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    target_type = Column(String(30), nullable=False, unique=True, comment="评价对象类型: course/instructor/training/training_base")
    description = Column(Text, nullable=True, comment="模板说明")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    dimensions = relationship("EvaluationDimension", back_populates="template", cascade="all, delete-orphan",
                              order_by="EvaluationDimension.sort_order")


class EvaluationDimension(Base):
    """评价维度"""

    __tablename__ = "evaluation_dimensions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("evaluation_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="维度名称")
    description = Column(String(500), nullable=True, comment="维度说明")
    sort_order = Column(Integer, default=0, comment="排序")
    weight = Column(Float, default=1.0, comment="权重")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("EvaluationTemplate", back_populates="dimensions")


class EvaluationTask(Base):
    """评价任务（手动发布或自动创建）"""

    __tablename__ = "evaluation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("evaluation_templates.id"), nullable=False)
    target_type = Column(String(30), nullable=False, comment="评价对象类型")
    target_id = Column(Integer, nullable=False, comment="被评对象ID")
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="SET NULL"), nullable=True, comment="关联培训班")
    title = Column(String(200), nullable=False, comment="任务标题")
    status = Column(String(20), default="active", comment="状态: draft/active/closed")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="截止时间")
    source = Column(String(20), default="manual", comment="来源: manual/auto")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_eval_task_target", "target_type", "target_id"),
    )

    template = relationship("EvaluationTemplate", foreign_keys=[template_id])
    records = relationship("EvaluationRecord", back_populates="task", cascade="all, delete-orphan")


class EvaluationRecord(Base):
    """评价记录"""

    __tablename__ = "evaluation_records"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("evaluation_templates.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("evaluation_tasks.id", ondelete="SET NULL"), nullable=True, comment="关联任务（自主填写为空）")
    target_type = Column(String(30), nullable=False)
    target_id = Column(Integer, nullable=False, comment="被评对象ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="评价人")
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="SET NULL"), nullable=True, comment="关联培训班上下文")
    comment = Column(Text, nullable=True, comment="总体评语")
    avg_score = Column(Float, default=0, comment="各维度均分（冗余）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("template_id", "target_id", "user_id", "training_id", name="uq_eval_record"),
        Index("ix_eval_record_target", "target_type", "target_id"),
        Index("ix_eval_record_user", "user_id"),
    )

    template = relationship("EvaluationTemplate", foreign_keys=[template_id])
    task = relationship("EvaluationTask", back_populates="records")
    user = relationship("User", foreign_keys=[user_id])
    scores = relationship("EvaluationScore", back_populates="record", cascade="all, delete-orphan")


class EvaluationScore(Base):
    """维度评分"""

    __tablename__ = "evaluation_scores"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("evaluation_records.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension_id = Column(Integer, ForeignKey("evaluation_dimensions.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, default=0, comment="评分 0-5")

    record = relationship("EvaluationRecord", back_populates="scores")
    dimension = relationship("EvaluationDimension", foreign_keys=[dimension_id])
