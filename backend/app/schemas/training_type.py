"""
培训班类型管理相关的数据验证模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TrainingTypeCreate(BaseModel):
    """创建培训班类型请求"""
    name: str = Field(..., min_length=1, max_length=100, description="类型名称")
    code: str = Field(..., min_length=1, max_length=50, description="类型编码")
    description: Optional[str] = Field(None, description="描述")


class TrainingTypeUpdate(BaseModel):
    """更新培训班类型请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="类型名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class TrainingTypeResponse(BaseModel):
    """培训班类型响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
