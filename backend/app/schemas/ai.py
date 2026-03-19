"""
AI 任务相关的数据验证模型
"""
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


AITaskType = Literal["question_generation", "paper_assembly", "paper_generation"]
AITaskStatus = Literal["pending", "processing", "completed", "confirmed", "failed"]


class AITaskQuestionDraft(BaseModel):
    """AI 任务中的题目草稿"""

    temp_id: str = Field(..., description="任务内临时题目 ID")
    source_question_id: Optional[int] = Field(None, description="来源题目 ID，编辑原题时用于复用")
    origin: str = Field("generated", description="题目来源: generated/existing/manual")
    type: str = Field(..., description="题目类型: single/multi/judge")
    content: str = Field(..., description="题干")
    options: Optional[List[dict]] = Field(default=None, description="选项 [{key, text}]")
    answer: Any = Field(..., description="答案")
    explanation: Optional[str] = Field(None, description="解析")
    difficulty: int = Field(3, ge=1, le=5, description="难度")
    knowledge_point: Optional[str] = Field(None, description="知识点")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    score: int = Field(2, ge=1, description="分值")


class AITaskPaperDraft(BaseModel):
    """AI 任务中的试卷草稿"""

    title: str = Field(..., max_length=200, description="试卷名称")
    description: Optional[str] = Field(None, description="试卷说明")
    type: str = Field("formal", description="试卷类型: formal/quiz")
    duration: int = Field(60, ge=10, le=300, description="考试时长")
    passing_score: int = Field(60, ge=1, description="及格分")
    total_score: int = Field(0, ge=0, description="总分")
    questions: List[AITaskQuestionDraft] = Field(default_factory=list, description="试卷题目草稿")


class AIQuestionTaskCreateRequest(BaseModel):
    """AI 智能出题创建请求"""

    task_name: str = Field(..., max_length=200, description="任务名称")
    topic: str = Field(..., max_length=200, description="出题主题")
    source_text: Optional[str] = Field(None, max_length=4000, description="参考文本")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    question_count: int = Field(10, ge=1, le=50, description="题目数量（当前 AI 智能出题最多 20 题）")
    question_types: List[str] = Field(default_factory=list, description="题型列表（当前 AI 智能出题每次只能选择一种题型）")
    difficulty: int = Field(3, ge=1, le=5, description="整体难度")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    score: int = Field(2, ge=1, description="默认分值")
    requirements: Optional[str] = Field(None, max_length=1000, description="补充要求")


class AIPaperAssemblyTypeConfig(BaseModel):
    """AI 自动组卷题型配置"""

    type: str = Field(..., description="题目类型")
    count: int = Field(..., ge=1, le=50, description="题目数量")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="题型难度")
    score: int = Field(2, ge=1, description="单题分值")


class AIPaperAssemblyTaskCreateRequest(BaseModel):
    """AI 自动组卷创建请求"""

    task_name: str = Field(..., max_length=200, description="任务名称")
    paper_title: str = Field(..., max_length=200, description="试卷名称")
    paper_type: str = Field("formal", description="试卷类型: formal/quiz")
    description: Optional[str] = Field(None, description="试卷说明")
    duration: int = Field(60, ge=10, le=300, description="考试时长")
    passing_score: int = Field(60, ge=1, description="及格分")
    assembly_mode: str = Field("balanced", description="组卷模式: balanced/practice/exam")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    exclude_question_ids: List[int] = Field(default_factory=list, description="排除题目 ID 列表")
    type_configs: List[AIPaperAssemblyTypeConfig] = Field(default_factory=list, description="题型配置")
    requirements: Optional[str] = Field(None, max_length=1000, description="补充要求")


class AIPaperGenerationTaskCreateRequest(BaseModel):
    """AI 自动生成试卷创建请求"""

    task_name: str = Field(..., max_length=200, description="任务名称")
    paper_title: str = Field(..., max_length=200, description="试卷名称")
    paper_type: str = Field("formal", description="试卷类型: formal/quiz")
    description: Optional[str] = Field(None, description="试卷说明")
    duration: int = Field(60, ge=10, le=300, description="考试时长")
    passing_score: int = Field(60, ge=1, description="及格分")
    topic: str = Field(..., max_length=200, description="生成主题")
    source_text: Optional[str] = Field(None, max_length=4000, description="参考文本")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    difficulty: int = Field(3, ge=1, le=5, description="整体难度")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    type_configs: List[AIPaperAssemblyTypeConfig] = Field(default_factory=list, description="题型配置")
    requirements: Optional[str] = Field(None, max_length=1000, description="补充要求")


class AIQuestionTaskUpdateRequest(BaseModel):
    """AI 智能出题结果更新请求"""

    task_name: Optional[str] = Field(None, max_length=200, description="任务名称")
    questions: List[AITaskQuestionDraft] = Field(default_factory=list, description="更新后的题目草稿")


class AIPaperTaskUpdateRequest(BaseModel):
    """AI 试卷任务结果更新请求"""

    task_name: Optional[str] = Field(None, max_length=200, description="任务名称")
    paper_draft: AITaskPaperDraft = Field(..., description="更新后的试卷草稿")


class AITaskSummaryResponse(BaseModel):
    """AI 任务摘要响应"""

    id: int
    task_name: str
    task_type: AITaskType
    status: AITaskStatus
    item_count: int = 0
    paper_title: Optional[str] = None
    created_by: int
    confirmed_question_ids: List[int] = Field(default_factory=list)
    confirmed_paper_id: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIQuestionTaskDetailResponse(AITaskSummaryResponse):
    """AI 智能出题任务详情响应"""

    request_payload: AIQuestionTaskCreateRequest
    questions: List[AITaskQuestionDraft] = Field(default_factory=list)
    error_message: Optional[str] = None


class AIPaperAssemblyTaskDetailResponse(AITaskSummaryResponse):
    """AI 自动组卷任务详情响应"""

    request_payload: AIPaperAssemblyTaskCreateRequest
    paper_draft: Optional[AITaskPaperDraft] = None
    error_message: Optional[str] = None


class AIPaperGenerationTaskDetailResponse(AITaskSummaryResponse):
    """AI 自动生成试卷任务详情响应"""

    request_payload: AIPaperGenerationTaskCreateRequest
    paper_draft: Optional[AITaskPaperDraft] = None
    error_message: Optional[str] = None
