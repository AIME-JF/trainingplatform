"""
部门管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 用户部门关联表
user_departments = Table(
    'user_departments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('department_id', Integer, ForeignKey('departments.id'), primary_key=True)
)


class Department(Base):
    """部门表"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment='部门名称')
    code = Column(String(50), unique=True, index=True, nullable=False, comment='部门标识')
    parent_id = Column(Integer, ForeignKey('departments.id'), nullable=True, comment='父级部门ID')
    inherit_sub_permissions = Column(Boolean, default=False, comment='是否继承子部门权限')
    description = Column(Text, comment='部门描述')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')
    
    # 关联关系
    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent")
    users = relationship("User", secondary=user_departments, back_populates="departments")
    permissions = relationship("Permission", secondary="department_permissions", back_populates="departments") 