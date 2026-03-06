"""
人才库相关的数据验证模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class TalentResponse(BaseModel):
    """人才响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    police_id: Optional[str] = None
    departments: List[str] = []
    police_types: List[str] = []
    avatar: Optional[str] = None
    level: Optional[str] = None
    study_hours: float = 0
    exam_count: int = 0
    avg_score: float = 0
    tier: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TalentStatsResponse(BaseModel):
    """人才统计响应"""
    total: int = 0
    tier_distribution: List[Any] = []
    department_distribution: List[Any] = []
    avg_score: float = 0
    avg_study_hours: float = 0
