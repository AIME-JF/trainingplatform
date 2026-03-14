"""
角色管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class Role(Base):
    """角色表"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False, comment='角色编码')
    name = Column(String(100), nullable=False, comment='角色名称')
    description = Column(Text, comment='角色描述')
    is_active = Column(Boolean, default=True, comment='是否激活')
    data_scopes = Column(JSON, nullable=True, comment='数据范围列表')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')
    
    # 关联关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles") 
