"""
部门管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from .permission import PermissionResponse


class DepartmentCreate(BaseModel):
    """创建部门请求"""
    name: str = Field(..., min_length=2, max_length=100, description="部门名称")
    code: str = Field(..., min_length=2, max_length=50, description="部门标识")
    parent_id: Optional[int] = Field(None, description="父级部门ID，如果不设置，则表示根部门")
    inherit_sub_permissions: bool = Field(False, description="是否继承子部门权限")
    description: Optional[str] = Field(None, description="部门描述")
    permission_ids: Optional[List[int]] = Field([], description="权限ID列表")


class DepartmentUpdate(BaseModel):
    """更新部门请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="部门名称")
    parent_id: Optional[int] = Field(None, description="父级部门ID")
    inherit_sub_permissions: Optional[bool] = Field(None, description="是否继承子部门权限")
    description: Optional[str] = Field(None, description="部门描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class DepartmentPermissionUpdate(BaseModel):
    """更新部门权限请求"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class DepartmentSimpleResponse(BaseModel):
    """部门简单响应模型（不包含关联关系）"""
    id: int
    name: str
    code: str
    parent_id: Optional[int] = None
    inherit_sub_permissions: bool
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentResponse(BaseModel):
    """部门响应模型"""
    id: int
    name: str
    code: str
    parent_id: Optional[int] = None
    inherit_sub_permissions: bool
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    parent: Optional['DepartmentSimpleResponse'] = None
    children: List['DepartmentSimpleResponse'] = []
    permissions: List[PermissionResponse] = []
    
    model_config = ConfigDict(from_attributes=True) 