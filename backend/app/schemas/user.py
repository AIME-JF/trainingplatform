"""
用户权限管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from .role import RoleResponse, RoleSimpleResponse
from .department import DepartmentSimpleResponse


class TokenData(BaseModel):
    """JWT Token数据"""
    username: str
    user_id: int
    permissions: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    gender: Optional[str] = Field(None, description="性别")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    police_id: Optional[str] = Field(None, max_length=50, description="警号")
    unit: Optional[str] = Field(None, max_length=200, description="所属单位")
    police_type: Optional[str] = Field(None, max_length=50, description="警种")
    avatar: Optional[str] = Field(None, description="头像URL")
    join_date: Optional[date] = Field(None, description="入警日期")
    level: Optional[str] = Field(None, description="学员等级")
    role_ids: Optional[List[int]] = Field([], description="角色ID列表")
    department_ids: Optional[List[int]] = Field([], description="部门ID列表")


class UserUpdate(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    gender: Optional[str] = Field(None, description="性别")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: Optional[bool] = Field(None, description="是否激活")
    police_id: Optional[str] = Field(None, max_length=50, description="警号")
    unit: Optional[str] = Field(None, max_length=200, description="所属单位")
    police_type: Optional[str] = Field(None, max_length=50, description="警种")
    avatar: Optional[str] = Field(None, description="头像URL")
    join_date: Optional[date] = Field(None, description="入警日期")
    level: Optional[str] = Field(None, description="学员等级")


class UserRoleUpdate(BaseModel):
    """更新用户角色请求"""
    role_ids: List[int] = Field(..., description="角色ID列表")


class UserDepartmentUpdate(BaseModel):
    """更新用户部门请求"""
    department_ids: List[int] = Field(..., description="部门ID列表")


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class UserSimpleResponse(BaseModel):
    """用户简单响应模型（角色不包含权限列表）"""
    id: int
    username: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    police_id: Optional[str] = None
    unit: Optional[str] = None
    police_type: Optional[str] = None
    avatar: Optional[str] = None
    join_date: Optional[date] = None
    level: Optional[str] = None
    study_hours: float = 0
    exam_count: int = 0
    avg_score: float = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[RoleSimpleResponse] = []
    departments: List[DepartmentSimpleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """用户响应模型（角色包含权限列表）"""
    id: int
    username: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    police_id: Optional[str] = None
    unit: Optional[str] = None
    police_type: Optional[str] = None
    avatar: Optional[str] = None
    join_date: Optional[date] = None
    level: Optional[str] = None
    study_hours: float = 0
    exam_count: int = 0
    avg_score: float = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[RoleResponse] = []
    departments: List[DepartmentSimpleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    
    model_config = ConfigDict(from_attributes=True) 