"""
警种管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 用户警种关联表
user_police_types = Table(
    'user_police_types',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('police_type_id', Integer, ForeignKey('police_types.id'), primary_key=True)
)


class PoliceType(Base):
    """警种表"""
    __tablename__ = 'police_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment='警种名称')
    code = Column(String(50), unique=True, index=True, nullable=False, comment='警种编码')
    description = Column(Text, comment='描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    users = relationship("User", secondary=user_police_types, back_populates="police_types")
