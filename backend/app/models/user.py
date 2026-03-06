"""
用户权限管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 从其他模块导入关联表
from .role import user_roles
from .department import user_departments
from .police_type import user_police_types


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='加盐hash后的密码')
    nickname = Column(String(100), comment='昵称')
    gender = Column(String(10), comment='性别')
    email = Column(String(100), unique=True, index=True, comment='邮箱')
    phone = Column(String(20), unique=True, index=True, comment='手机号')
    is_active = Column(Boolean, default=True, comment='是否激活')

    # 警务相关字段
    police_id = Column(String(50), unique=True, index=True, nullable=True, comment='警号')
    avatar = Column(String(500), nullable=True, comment='头像URL')
    join_date = Column(Date, nullable=True, comment='入警日期')
    level = Column(String(50), nullable=True, comment='学员等级')
    study_hours = Column(Float, default=0, comment='学习总时长')
    exam_count = Column(Integer, default=0, comment='考试次数')
    avg_score = Column(Float, default=0, comment='平均分')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    departments = relationship("Department", secondary=user_departments, back_populates="users")
    police_types = relationship("PoliceType", secondary=user_police_types, back_populates="users")
    instructor_profile = relationship("InstructorProfile", back_populates="user", uselist=False)