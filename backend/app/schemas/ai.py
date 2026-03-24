"""
AI 任务相关的数据验证模型
"""
from datetime import date as DateType
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .training import TrainingCourseCreate, TrainingScheduleRuleConfig


AITaskType = Literal[
    "question_generation",
    "paper_assembly",
    "paper_generation",
    "schedule_generation",
    "personal_training_plan_generation",
]
AITaskStatus = Literal["pending", "processing", "completed", "confirmed", "failed"]
AIScheduleTaskStage = Literal["rule_parsing", "rule_confirmation", "schedule_generation", "schedule_confirmation"]


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
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    score: int = Field(2, ge=1, description="分值")

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_knowledge_point(cls, value: Any):
        if not isinstance(value, dict):
            return value
        if "knowledge_points" in value or "knowledgePoints" in value:
            return value

        legacy_value = value.get("knowledge_point", value.get("knowledgePoint"))
        if legacy_value in (None, ""):
            return value

        payload = dict(value)
        payload["knowledge_points"] = legacy_value if isinstance(legacy_value, list) else [legacy_value]
        return payload

    @field_validator("knowledge_points", mode="before")
    @classmethod
    def validate_knowledge_points(cls, value: Any) -> List[str]:
        if value is None:
            return []
        raw_items = [value] if isinstance(value, str) else list(value or [])
        normalized: List[str] = []
        seen = set()
        for raw_item in raw_items:
            item = str(raw_item or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized.append(item[:100])
        return normalized


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


class AIScheduleUnavailableSlot(BaseModel):
    """排课不可用时间段"""

    date: DateType = Field(..., description="不可用日期")
    time_range: str = Field(..., description="时间段 HH:MM~HH:MM")
    label: Optional[str] = Field(None, description="标识，如教官/场地名")


class AIScheduleCourseTypeTimePreference(BaseModel):
    """课程类型的时间偏好"""

    course_type: Literal["theory", "practice"] = Field(..., description="课程类型")
    start_time: str = Field(..., description="开始时间 HH:MM")
    end_time: str = Field(..., description="结束时间 HH:MM")
    weekdays: List[int] = Field(default_factory=list, description="适用星期，1-7 表示周一到周日")
    priority: Literal["prefer", "only"] = Field("prefer", description="prefer=优先，only=仅允许")
    label: Optional[str] = Field(None, description="规则标签")


class AIScheduleExamWeekFocus(BaseModel):
    """考前强化偏好"""

    course_type: Optional[Literal["theory", "practice"]] = Field(None, description="优先强化的课程类型")
    course_keywords: List[str] = Field(default_factory=list, description="优先强化的课程关键词")
    days_before_exam: int = Field(7, ge=1, le=30, description="考试前多少天内优先安排")
    label: Optional[str] = Field(None, description="规则标签")


class AIScheduleTaskConstraintPayload(BaseModel):
    """排课约束参数"""

    daily_max_hours: float = Field(6, ge=1, le=12, description="单日最大课时")
    theory_practice_ratio: Optional[str] = Field(None, description="理论/实操比例，如 4:6")
    avoid_exam_days: bool = Field(True, description="是否避开考试日")
    fixed_course_keys: List[str] = Field(default_factory=list, description="固定课程键列表")
    blocked_time_slots: List[AIScheduleUnavailableSlot] = Field(default_factory=list, description="全局禁排时间")
    course_type_time_preferences: List[AIScheduleCourseTypeTimePreference] = Field(default_factory=list, description="课程类型时段偏好")
    instructor_unavailable_slots: List[AIScheduleUnavailableSlot] = Field(default_factory=list, description="教官不可用时间")
    location_unavailable_slots: List[AIScheduleUnavailableSlot] = Field(default_factory=list, description="场地不可用时间")
    exam_week_focus: Optional[AIScheduleExamWeekFocus] = Field(None, description="考前强化偏好")


class AIScheduleTaskCreateRequest(BaseModel):
    """AI 排课任务创建请求"""

    task_name: str = Field(..., max_length=200, description="任务名称")
    training_id: int = Field(..., description="培训班 ID")
    natural_language_prompt: Optional[str] = Field(None, max_length=4000, description="自然语言排课要求")
    scope_type: Literal["all", "current_week", "unscheduled"] = Field("all", description="排课范围")
    scope_start_date: Optional[DateType] = Field(None, description="指定周起始日期")
    goal: Literal["balanced", "practice_first", "theory_first", "exam_intensive"] = Field("balanced", description="排课目标")
    planning_mode: Literal["auto", "fill_all_days", "fill_workdays", "by_hours"] = Field(
        "auto",
        description="排课方式: auto/fill_all_days/fill_workdays/by_hours",
    )
    overwrite_existing_schedule: bool = Field(False, description="是否覆盖当前课表")
    parsed_request_confirmed: bool = Field(False, description="是否已确认解析结果，执行时不再二次猜测")
    constraint_payload: AIScheduleTaskConstraintPayload = Field(default_factory=AIScheduleTaskConstraintPayload, description="排课约束")
    schedule_rule_override: Optional[TrainingScheduleRuleConfig] = Field(None, description="任务级排课规则覆盖")
    notes: Optional[str] = Field(None, max_length=1000, description="补充说明")


class AIScheduleConflictItem(BaseModel):
    """排课冲突项"""

    severity: Literal["error", "warning"] = Field("error", description="冲突级别")
    conflict_type: str = Field(..., description="冲突类型")
    course_key: Optional[str] = Field(None, description="课程键")
    session_id: Optional[str] = Field(None, description="课次键")
    message: str = Field(..., description="冲突说明")
    suggestion: Optional[str] = Field(None, description="建议处理方式")


class AISchedulePlanMetrics(BaseModel):
    """排课方案指标"""

    total_sessions: int = 0
    total_hours: float = 0
    theory_hours: float = 0
    practice_hours: float = 0
    covered_days: int = 0
    instructor_load_index: float = 0


class AISchedulePlan(BaseModel):
    """排课方案"""

    plan_id: str = Field(..., description="方案标识")
    title: str = Field(..., max_length=100, description="方案标题")
    summary: Optional[str] = Field(None, description="方案摘要")
    score: float = Field(0, description="方案分数")
    courses: List[TrainingCourseCreate] = Field(default_factory=list, description="方案课程清单")
    metrics: AISchedulePlanMetrics = Field(default_factory=AISchedulePlanMetrics, description="方案指标")


class AIScheduleTaskUpdateRequest(BaseModel):
    """AI 排课任务结果更新请求"""

    task_name: Optional[str] = Field(None, max_length=200, description="任务名称")
    main_plan: AISchedulePlan = Field(..., description="主方案")
    alternative_plans: List[AISchedulePlan] = Field(default_factory=list, description="备选方案")
    conflicts: List[AIScheduleConflictItem] = Field(default_factory=list, description="冲突清单")
    explanation: Optional[str] = Field(None, max_length=4000, description="方案说明")


class AIPersonalTrainingTaskCreateRequest(BaseModel):
    """AI 个性化训练任务创建请求"""

    task_name: str = Field(..., max_length=200, description="任务名称")
    training_id: int = Field(..., description="培训班 ID")
    target_user_id: int = Field(..., description="目标学员 ID")
    plan_goal: str = Field("补齐短板，稳步提升", max_length=200, description="训练目标")
    plan_cycle_days: int = Field(14, ge=7, le=90, description="方案周期（天）")
    weekly_sessions: int = Field(3, ge=1, le=14, description="每周训练频次")
    focus_mode: Literal["auto", "theory", "practice", "exam"] = Field("auto", description="聚焦方向")
    notes: Optional[str] = Field(None, max_length=1000, description="补充说明")


class AIPersonalTrainingPortraitTag(BaseModel):
    """个训画像标签"""

    code: str = Field(..., description="标签编码")
    label: str = Field(..., description="标签名称")
    level: Literal["low", "medium", "high"] = Field("medium", description="风险等级")
    reason: str = Field(..., description="标签依据")


class AIPersonalTrainingPortraitEvidence(BaseModel):
    """个训画像依据"""

    source: str = Field(..., description="数据来源")
    label: str = Field(..., description="指标名称")
    value: str = Field(..., description="指标值")


class AIPersonalTrainingPortrait(BaseModel):
    """个训画像"""

    user_id: int = Field(..., description="学员 ID")
    user_name: str = Field(..., description="学员名称")
    training_id: int = Field(..., description="培训班 ID")
    training_name: str = Field(..., description="培训班名称")
    attendance_rate: float = Field(0, description="出勤率")
    completed_sessions: int = Field(0, description="完成课次")
    total_sessions: int = Field(0, description="总课次")
    evaluation_score: float = Field(0, description="评课均分")
    avg_exam_score: float = Field(0, description="平均考试分")
    recent_exam_score: float = Field(0, description="最近一次考试分")
    study_progress: float = Field(0, description="学习进度")
    total_study_hours: float = Field(0, description="学习时长")
    preferred_resource_tags: List[str] = Field(default_factory=list, description="资源偏好")
    tags: List[AIPersonalTrainingPortraitTag] = Field(default_factory=list, description="画像标签")
    evidence: List[AIPersonalTrainingPortraitEvidence] = Field(default_factory=list, description="画像依据")


class AIPersonalTrainingAction(BaseModel):
    """个训动作项"""

    title: str = Field(..., description="动作标题")
    description: str = Field(..., description="动作说明")
    frequency: str = Field(..., description="执行频次")
    duration_minutes: int = Field(..., ge=10, le=240, description="单次时长")
    emphasis: Optional[str] = Field(None, description="强调点")
    execution_tips: Optional[str] = Field(None, description="执行建议")


class AIPersonalTrainingResourceRecommendation(BaseModel):
    """个训资源推荐"""

    resource_id: int = Field(..., description="资源 ID")
    title: str = Field(..., description="资源标题")
    score: float = Field(0, description="推荐分")
    reason: str = Field(..., description="推荐理由")
    tag_names: List[str] = Field(default_factory=list, description="关联标签")


class AIPersonalTrainingPlan(BaseModel):
    """个训方案"""

    title: str = Field(..., description="方案标题")
    cycle_days: int = Field(..., ge=7, le=90, description="方案周期")
    weekly_sessions: int = Field(..., ge=1, le=14, description="每周频次")
    objectives: List[str] = Field(default_factory=list, description="训练目标")
    actions: List[AIPersonalTrainingAction] = Field(default_factory=list, description="训练动作")
    resource_recommendations: List[AIPersonalTrainingResourceRecommendation] = Field(default_factory=list, description="资源推荐")
    coach_tips: List[str] = Field(default_factory=list, description="教官建议")
    student_tips: List[str] = Field(default_factory=list, description="学员建议")
    summary: Optional[str] = Field(None, description="方案摘要")


class AIPersonalTrainingTaskUpdateRequest(BaseModel):
    """AI 个训任务结果更新请求"""

    task_name: Optional[str] = Field(None, max_length=200, description="任务名称")
    portrait: AIPersonalTrainingPortrait = Field(..., description="画像结果")
    plan: AIPersonalTrainingPlan = Field(..., description="训练方案")


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
    task_stage: Optional[str] = None
    item_count: int = 0
    paper_title: Optional[str] = None
    training_id: Optional[int] = None
    training_name: Optional[str] = None
    target_user_id: Optional[int] = None
    target_user_name: Optional[str] = None
    summary_text: Optional[str] = None
    created_by: int
    confirmed_question_ids: List[int] = Field(default_factory=list)
    confirmed_paper_id: Optional[int] = None
    confirmed_snapshot_id: Optional[int] = None
    can_delete: bool = False
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


class AIScheduleTaskDetailResponse(AITaskSummaryResponse):
    """AI 排课任务详情响应"""

    request_payload: AIScheduleTaskCreateRequest
    main_plan: Optional[AISchedulePlan] = None
    alternative_plans: List[AISchedulePlan] = Field(default_factory=list)
    conflicts: List[AIScheduleConflictItem] = Field(default_factory=list)
    explanation: Optional[str] = None
    parse_summary: Optional[str] = None
    parse_warnings: List[str] = Field(default_factory=list)
    understood_items: List[str] = Field(default_factory=list)
    training_rule_config: Optional[TrainingScheduleRuleConfig] = None
    effective_rule_config: Optional[TrainingScheduleRuleConfig] = None
    error_message: Optional[str] = None


class AIScheduleParsePreviewResponse(BaseModel):
    """AI 排课解析预览响应"""

    request_payload: AIScheduleTaskCreateRequest
    parse_summary: Optional[str] = None
    parse_warnings: List[str] = Field(default_factory=list)
    understood_items: List[str] = Field(default_factory=list)
    training_rule_config: TrainingScheduleRuleConfig = Field(default_factory=TrainingScheduleRuleConfig)
    effective_rule_config: TrainingScheduleRuleConfig = Field(default_factory=TrainingScheduleRuleConfig)


class AIPersonalTrainingTaskDetailResponse(AITaskSummaryResponse):
    """AI 个训任务详情响应"""

    request_payload: AIPersonalTrainingTaskCreateRequest
    portrait: Optional[AIPersonalTrainingPortrait] = None
    plan: Optional[AIPersonalTrainingPlan] = None
    error_message: Optional[str] = None
