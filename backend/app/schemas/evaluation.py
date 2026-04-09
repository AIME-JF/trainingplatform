"""
评价模块数据验证模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ========== 维度 ==========

class EvaluationDimensionCreate(BaseModel):
    name: str = Field(..., max_length=100, description="维度名称")
    description: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(0)
    weight: float = Field(1.0, ge=0)


class EvaluationDimensionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    weight: Optional[float] = Field(None, ge=0)


class EvaluationDimensionResponse(BaseModel):
    id: int
    template_id: int
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    weight: float = 1.0

    model_config = ConfigDict(from_attributes=True)


# ========== 模板 ==========

class EvaluationTemplateResponse(BaseModel):
    id: int
    name: str
    target_type: str
    description: Optional[str] = None
    enabled: bool = True
    dimensions: List[EvaluationDimensionResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    enabled: Optional[bool] = None


# ========== 任务 ==========

class EvaluationTaskCreate(BaseModel):
    training_id: int = Field(..., description="培训班ID")
    title: str = Field(..., max_length=200, description="任务标题")
    status: str = Field("active", description="状态: draft/active/closed")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class EvaluationTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class EvaluationTaskItemResponse(BaseModel):
    id: int
    task_id: int
    target_type: str
    target_id: int
    target_name: Optional[str] = None
    sort_order: int = 0
    dimensions: List[EvaluationDimensionResponse] = Field(default_factory=list)
    completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class EvaluationTaskResponse(BaseModel):
    id: int
    template_id: int
    target_type: str
    target_id: int
    training_id: Optional[int] = None
    training_name: Optional[str] = None
    title: str
    status: str = "active"
    source: str = "manual"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    record_count: int = 0
    item_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class EvaluationTaskDetailResponse(BaseModel):
    id: int
    title: str
    training_id: Optional[int] = None
    training_name: Optional[str] = None
    status: str = "active"
    items: List[EvaluationTaskItemResponse] = Field(default_factory=list)
    completed: bool = False

    model_config = ConfigDict(from_attributes=True)


# ========== 评价提交 ==========

class EvaluationScoreItem(BaseModel):
    dimension_id: int
    score: int = Field(..., ge=0, le=5)


class EvaluationSubmitItem(BaseModel):
    target_type: str = Field(..., description="评价对象类型")
    target_id: int = Field(..., description="被评对象ID")
    scores: List[EvaluationScoreItem] = Field(..., min_length=1)
    comment: Optional[str] = Field(None, max_length=1000, description="评语")


class EvaluationSubmit(BaseModel):
    task_id: int = Field(..., description="评价任务ID")
    items: List[EvaluationSubmitItem] = Field(..., min_length=1, description="各对象的评分数据")


# ========== 评价记录 ==========

class EvaluationScoreResponse(BaseModel):
    id: int
    dimension_id: int
    dimension_name: Optional[str] = None
    score: int = 0

    model_config = ConfigDict(from_attributes=True)


class EvaluationRecordResponse(BaseModel):
    id: int
    template_id: int
    task_id: Optional[int] = None
    target_type: str
    target_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    training_id: Optional[int] = None
    comment: Optional[str] = None
    avg_score: float = 0
    scores: List[EvaluationScoreResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== 统计 ==========

class EvaluationDimensionStat(BaseModel):
    dimension_id: int
    dimension_name: str
    avg_score: float = 0
    count: int = 0


class EvaluationSummaryResponse(BaseModel):
    target_type: str
    target_id: int
    total_count: int = 0
    overall_avg: float = 0
    dimensions: List[EvaluationDimensionStat] = Field(default_factory=list)
