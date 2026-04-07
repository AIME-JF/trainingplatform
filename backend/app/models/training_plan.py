"""
培训计划管理模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database import Base


class TrainingPlan(Base):
    """培训计划表"""

    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(String(4), nullable=False, comment="培训年度")
    name = Column(String(70), nullable=False, comment="培训班名称")
    category = Column(String(50), nullable=True, comment="培训类别")
    time_info = Column(String(10), nullable=True, comment="时间")
    organizer = Column(String(50), nullable=True, comment="主办单位")
    location = Column(String(50), nullable=True, comment="地点")
    days_per_period = Column(Integer, nullable=True, comment="每期天数")
    total_periods = Column(Integer, nullable=True, comment="合计期数")
    participant_count = Column(Integer, nullable=True, comment="参训人数")
    staff_count = Column(Integer, nullable=True, comment="工作人员数")
    training_cost = Column(Numeric(12, 2), nullable=True, comment="培训费用（万元）")
    instructor_cost = Column(Numeric(12, 2), nullable=True, comment="师资费（万元）")
    other_funding = Column(String(10), nullable=True, comment="其他经费来源（万元）")
    purpose = Column(String(200), nullable=True, comment="培训目的")
    target_audience = Column(String(200), nullable=True, comment="培训对象")
    content = Column(String(200), nullable=True, comment="内容")
    notes = Column(String(200), nullable=True, comment="备注")

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index("ix_training_plans_year", "year"),
        Index("ix_training_plans_created_by", "created_by"),
    )
