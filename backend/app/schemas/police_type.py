"""
警种管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PoliceTypeCreate(BaseModel):
    """创建警种请求"""
    name: str = Field(..., min_length=1, max_length=100, description="警种名称")
    code: str = Field(..., min_length=1, max_length=50, description="警种编码")
    description: Optional[str] = Field(None, description="描述")


class PoliceTypeUpdate(BaseModel):
    """更新警种请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="警种名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PoliceTypeSimpleResponse(BaseModel):
    """警种简单响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PoliceTypeResponse(BaseModel):
    """警种响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
