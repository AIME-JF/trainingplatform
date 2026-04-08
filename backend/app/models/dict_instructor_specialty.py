"""
教官专长方向字典表
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class DictInstructorSpecialty(Base):
    """教官专长方向字典"""

    __tablename__ = "dict_instructor_specialties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, comment="专长方向名称")
    sort_order = Column(Integer, default=0, comment="排序序号")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
