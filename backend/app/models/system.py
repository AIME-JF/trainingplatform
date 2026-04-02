"""
系统配置相关数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ConfigFormat(enum.Enum):
    """配置格式枚举"""
    SHORT_TEXT = "short_text"      # 短文本
    LONG_TEXT = "long_text"        # 长文本
    INTEGER = "integer"            # 整数
    FLOAT = "float"                # 浮点数
    BOOLEAN = "boolean"            # 布尔
    LIST = "list"                  # 列表
    SELECT = "select"              # 下拉选择
    MULTI_SELECT = "multi_select"  # 多选
    PASSWORD = "password"          # 密码（前端隐藏显示）


class SystemMeta(Base):
    """元数据模型"""
    __tablename__ = "system_meta"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, comment="元数据键")
    value = Column(Text, comment="元数据值")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class ConfigGroup(Base):
    """配置组模型"""
    __tablename__ = "config_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), nullable=False, comment="配置组名")
    group_key = Column(String(50), unique=True, nullable=False, index=True, comment="配置组标识")
    group_description = Column(Text, comment="配置组描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    configs = relationship("Config", back_populates="group", cascade="all, delete-orphan")


class Config(Base):
    """配置模型"""
    __tablename__ = "configs"

    # 添加联合唯一约束
    __table_args__ = (
        UniqueConstraint('group_id', 'config_key', name='uq_config_group_key'),
        {'comment': '系统配置表'},
    ) 

    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), nullable=False, comment="配置名")
    config_key = Column(String(50), nullable=False, index=True, comment="配置标识")
    config_description = Column(Text, comment="配置描述")
    config_format = Column(Enum(ConfigFormat), nullable=False, comment="配置格式")
    config_value = Column(JSON, comment="配置值")
    is_required = Column(Boolean, default=False, comment="是否必填")
    is_public = Column(Boolean, default=False, comment="是否公开")
    group_id = Column(Integer, ForeignKey("config_groups.id"), nullable=False, comment="配置组ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    group = relationship("ConfigGroup", back_populates="configs")


class DashboardModuleConfig(Base):
    """看板模块配置表"""
    __tablename__ = "dashboard_module_configs"

    id = Column(Integer, primary_key=True, index=True)
    module_key = Column(String(50), unique=True, nullable=False, index=True, comment="模块标识")
    module_name = Column(String(100), nullable=False, comment="模块名称")
    module_description = Column(Text, comment="模块描述")
    category = Column(String(50), nullable=False, default="general", comment="模块分类: general/training")
    visible_role_codes = Column(JSON, nullable=False, default=list, comment="可见角色编码列表")
    sort_order = Column(Integer, default=0, comment="排序号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
