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


class PermissionGroup(Base):
    """权限组表"""
    __tablename__ = 'permission_groups'

    id = Column(Integer, primary_key=True, index=True)
    group_key = Column(String(100), unique=True, nullable=False, index=True, comment='权限组标识')
    group_name = Column(String(100), nullable=False, comment='权限组名称')
    description = Column(Text, comment='权限组描述')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关联关系
    permissions = relationship("Permission", back_populates="permission_group")


class Permission(Base):
    """权限表"""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(200), nullable=False, comment='接口路径')
    code = Column(String(100), unique=True, index=True, nullable=False, comment='权限编码')
    group = Column(String(100), nullable=False, index=True, server_default='SYSTEM', comment='权限分组标识（冗余，与 group_key 一致）')
    group_id = Column(Integer, ForeignKey('permission_groups.id'), nullable=True, comment='所属权限组')
    description = Column(Text, comment='权限描述')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    permission_group = relationship("PermissionGroup", back_populates="permissions")
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    departments = relationship("Department", secondary=department_permissions, back_populates="permissions")
