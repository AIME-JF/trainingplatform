"""
角色管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .permission import PermissionResponse


ROLE_DATA_SCOPE_ALL = "all"
ROLE_DATA_SCOPE_DEPARTMENT = "department"
ROLE_DATA_SCOPE_DEPARTMENT_AND_SUB = "department_and_sub"
ROLE_DATA_SCOPE_POLICE_TYPE = "police_type"
ROLE_DATA_SCOPE_SELF = "self"
ROLE_DATA_SCOPE_CHOICES = {
    ROLE_DATA_SCOPE_ALL,
    ROLE_DATA_SCOPE_DEPARTMENT,
    ROLE_DATA_SCOPE_DEPARTMENT_AND_SUB,
    ROLE_DATA_SCOPE_POLICE_TYPE,
    ROLE_DATA_SCOPE_SELF,
}


class RoleDataScopeMixin(BaseModel):
    data_scopes: List[str] = Field(default_factory=list, description="数据范围列表")

    @field_validator("data_scopes", mode="before")
    @classmethod
    def validate_data_scopes(cls, value: Optional[List[str]]) -> List[str]:
        normalized: List[str] = []
        for raw_item in value or []:
            item = str(raw_item or "").strip()
            if not item:
                continue
            if item not in ROLE_DATA_SCOPE_CHOICES:
                raise ValueError(f"不支持的数据范围: {item}")
            if item not in normalized:
                normalized.append(item)
        return normalized


class RoleCreate(RoleDataScopeMixin):
    """创建角色请求"""
    code: str = Field(..., min_length=2, max_length=50, description="角色编码")
    name: str = Field(..., min_length=2, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permission_ids: Optional[List[int]] = Field([], description="权限ID列表")


class RoleUpdate(RoleDataScopeMixin):
    """更新角色请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class RolePermissionUpdate(BaseModel):
    """更新角色权限请求"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class RoleSimpleResponse(RoleDataScopeMixin):
    """角色简单响应模型（不含权限列表）"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponse(RoleDataScopeMixin):
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
