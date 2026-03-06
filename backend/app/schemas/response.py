from typing import Optional, Any, TypeVar, Generic, List
from pydantic import BaseModel, Field


T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式"""
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    items: List[T] = Field(..., description="数据列表")

