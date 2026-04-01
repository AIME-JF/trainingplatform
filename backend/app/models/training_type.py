"""
培训班类型管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class TrainingType(Base):
    """培训班类型表"""
    __tablename__ = 'training_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment='类型名称')
    code = Column(String(50), unique=True, index=True, nullable=False, comment='类型编码')
    description = Column(Text, comment='描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')
