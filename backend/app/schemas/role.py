"""
角色管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from .permission import PermissionResponse


class RoleCreate(BaseModel):
    """创建角色请求"""
    code: str = Field(..., min_length=2, max_length=50, description="角色编码")
    name: str = Field(..., min_length=2, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permission_ids: Optional[List[int]] = Field([], description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class RolePermissionUpdate(BaseModel):
    """更新角色权限请求"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class RoleSimpleResponse(BaseModel):
    """角色简单响应模型（不含权限列表）"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    """角色响应模型（含权限列表）"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = []
    
    model_config = ConfigDict(from_attributes=True) 