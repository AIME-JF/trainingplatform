"""
知识点相关的数据验证模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KnowledgePointCreate(BaseModel):
    """创建知识点"""

    name: str = Field(..., max_length=100, description="知识点名称")
    description: Optional[str] = Field(None, max_length=500, description="知识点描述")
    is_active: bool = Field(True, description="是否启用")


class KnowledgePointUpdate(BaseModel):
    """更新知识点"""

    name: Optional[str] = Field(None, max_length=100, description="知识点名称")
    description: Optional[str] = Field(None, max_length=500, description="知识点描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class KnowledgePointSimpleResponse(BaseModel):
    """知识点简要信息"""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class KnowledgePointResponse(KnowledgePointSimpleResponse):
    """知识点响应"""

    description: Optional[str] = None
    is_active: bool = True
    question_count: int = 0
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
