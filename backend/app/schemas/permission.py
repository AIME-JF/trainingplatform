"""
权限管理相关的数据验证模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PermissionCreate(BaseModel):
    """创建权限请求"""
    path: str = Field(..., description="接口路径")
    code: str = Field(..., min_length=2, max_length=100, description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")


class PermissionUpdate(BaseModel):
    """更新权限请求"""
    path: Optional[str] = Field(None, description="接口路径")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PermissionResponse(BaseModel):
    """权限响应模型"""
    id: int
    path: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True) 