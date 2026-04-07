"""
培训计划管理相关的数据验证模型
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class TrainingPlanCreate(BaseModel):
    """创建培训计划"""
    year: str = Field(..., max_length=4, description="培训年度")
    name: str = Field(..., max_length=70, description="培训班名称")
    category: Optional[str] = Field(None, max_length=50, description="培训类别")
    time_info: Optional[str] = Field(None, max_length=10, description="时间")
    organizer: Optional[str] = Field(None, max_length=50, description="主办单位")
    location: Optional[str] = Field(None, max_length=50, description="地点")
    days_per_period: Optional[int] = Field(None, description="每期天数")
    total_periods: Optional[int] = Field(None, description="合计期数")
    participant_count: Optional[int] = Field(None, description="参训人数")
    staff_count: Optional[int] = Field(None, description="工作人员数")
    training_cost: Optional[Decimal] = Field(None, description="培训费用（万元）")
    instructor_cost: Optional[Decimal] = Field(None, description="师资费（万元）")
    other_funding: Optional[str] = Field(None, max_length=10, description="其他经费来源（万元）")
    purpose: Optional[str] = Field(None, max_length=200, description="培训目的")
    target_audience: Optional[str] = Field(None, max_length=200, description="培训对象")
    content: Optional[str] = Field(None, max_length=200, description="内容")
    notes: Optional[str] = Field(None, max_length=200, description="备注")


class TrainingPlanUpdate(BaseModel):
    """更新培训计划"""
    year: Optional[str] = Field(None, max_length=4)
    name: Optional[str] = Field(None, max_length=70)
    category: Optional[str] = Field(None, max_length=50)
    time_info: Optional[str] = Field(None, max_length=10)
    organizer: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=50)
    days_per_period: Optional[int] = None
    total_periods: Optional[int] = None
    participant_count: Optional[int] = None
    staff_count: Optional[int] = None
    training_cost: Optional[Decimal] = None
    instructor_cost: Optional[Decimal] = None
    other_funding: Optional[str] = Field(None, max_length=10)
    purpose: Optional[str] = Field(None, max_length=200)
    target_audience: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=200)


class TrainingPlanResponse(BaseModel):
    """培训计划响应"""
    id: int
    year: str
    name: str
    category: Optional[str] = None
    time_info: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    days_per_period: Optional[int] = None
    total_periods: Optional[int] = None
    participant_count: Optional[int] = None
    staff_count: Optional[int] = None
    training_cost: Optional[Decimal] = None
    instructor_cost: Optional[Decimal] = None
    other_funding: Optional[str] = None
    purpose: Optional[str] = None
    target_audience: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
