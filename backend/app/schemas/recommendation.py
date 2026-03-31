"""
资源推荐与行为埋点相关数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceBehaviorEventCreate(BaseModel):
    event_type: str = Field(..., description='事件类型')
    watch_seconds: int = Field(0, ge=0, description='观看时长')
    context_json: Optional[dict] = Field(None, description='上下文')


class ResourceRecommendationItem(BaseModel):
    resource_id: int
    score: float


class ResourceRecommendationFeedResponse(BaseModel):
    items: List[ResourceRecommendationItem]
    page: int
    size: int
    total: int


class RecommendationScoreBreakdown(BaseModel):
    resource_id: int
    score: float
    police_type_score: float
    department_score: float
    interest_score: float
    freshness_score: float
    popularity_score: float
    updated_at: Optional[datetime] = None
