"""
权限管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# 部门权限关联表
department_permissions = Table(
    'department_permissions',
    Base.metadata,
    Column('department_id', Integer, ForeignKey('departments.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Permission(Base):
    """权限表"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(200), nullable=False, comment='接口路径')
    code = Column(String(100), unique=True, index=True, nullable=False, comment='权限编码')
    description = Column(Text, comment='权限描述')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')
    
    # 关联关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    departments = relationship("Department", secondary=department_permissions, back_populates="permissions") 