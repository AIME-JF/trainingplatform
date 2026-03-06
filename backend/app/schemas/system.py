"""
系统配置相关数据模式
"""
from typing import Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.system import ConfigFormat


# 配置组相关模式
class ConfigGroupBase(BaseModel):
    """配置组基础模式"""
    group_name: str = Field(..., description="配置组名")
    group_key: str = Field(..., description="配置组标识")
    group_description: Optional[str] = Field(None, description="配置组描述")


class ConfigGroupCreate(ConfigGroupBase):
    """创建配置组模式"""
    pass


class ConfigGroupUpdate(BaseModel):
    """更新配置组模式"""
    group_name: Optional[str] = Field(None, description="配置组名")
    group_description: Optional[str] = Field(None, description="配置组描述")


class ConfigGroupResponse(ConfigGroupBase):
    """配置组响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 配置相关模式
class ConfigBase(BaseModel):
    """配置基础模式"""
    config_name: str = Field(..., description="配置名")
    config_key: str = Field(..., description="配置标识")
    config_description: Optional[str] = Field(None, description="配置描述")
    config_format: ConfigFormat = Field(..., description="配置格式")
    config_value: Optional[Any] = Field(None, description="配置值")
    is_required: bool = Field(False, description="是否必填")
    is_public: bool = Field(False, description="是否公开")
    group_id: int = Field(..., description="配置组ID")


class ConfigCreate(ConfigBase):
    """创建配置模式"""
    pass


class ConfigUpdate(BaseModel):
    """更新配置模式"""
    config_name: Optional[str] = Field(None, description="配置名")
    config_description: Optional[str] = Field(None, description="配置描述")
    config_format: Optional[ConfigFormat] = Field(None, description="配置格式")
    config_value: Optional[Any] = Field(None, description="配置值")
    is_required: Optional[bool] = Field(None, description="是否必填")
    is_public: Optional[bool] = Field(None, description="是否公开")
    group_id: Optional[int] = Field(None, description="配置组ID")


class ConfigResponse(ConfigBase):
    """配置响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    group: Optional[ConfigGroupResponse] = None

    class Config:
        from_attributes = True


# 配置组详情模式（包含配置列表）
class ConfigGroupDetailResponse(ConfigGroupResponse):
    """配置组详情响应模式"""
    configs: List[ConfigResponse] = []

    class Config:  # pyright: ignore[reportIncompatibleVariableOverride]
        from_attributes = True


# 公开配置响应模式
class PublicConfigResponse(BaseModel):
    """公开配置响应模式"""
    config_key: str = Field(..., description="配置标识")
    config_value: Optional[Any] = Field(None, description="配置值")
    config_format: ConfigFormat = Field(..., description="配置格式")
    group_key: str = Field(..., description="配置组标识")

    class Config:
        from_attributes = True 