"""
资源推荐与行为埋点相关数据模型
"""
from typing import Literal, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceBehaviorEventCreate(BaseModel):
    event_type: Literal['impression', 'click', 'play', 'complete', 'favorite'] = Field(..., description='事件类型')
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


class CommunityBoardOverviewResponse(BaseModel):
    submission_count: int = 0
    total_videos: int = 0
    total_plays: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    engagement_rate: float = 0
    completion_rate: float = 0


class CommunityBoardTrendItem(BaseModel):
    date: str
    plays: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class CommunityBoardInteractionItem(BaseModel):
    name: str
    value: int = 0


class CommunityBoardVideoItem(BaseModel):
    id: int
    title: str
    category: str = '视频'
    uploader_name: Optional[str] = None
    plays: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0
    completion_rate: float = 0


class CommunityBoardDashboardResponse(BaseModel):
    overview: CommunityBoardOverviewResponse
    trend: List[CommunityBoardTrendItem]
    interaction_distribution: List[CommunityBoardInteractionItem]
    top_videos: List[CommunityBoardVideoItem]
    latest_videos: List[CommunityBoardVideoItem]


class RecommendationScoreBreakdown(BaseModel):
    resource_id: int
    score: float
    police_type_score: float
    department_score: float
    interest_score: float
    freshness_score: float
    popularity_score: float
    updated_at: Optional[datetime] = None
