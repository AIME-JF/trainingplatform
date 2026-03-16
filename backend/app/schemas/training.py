"""
培训管理相关的数据验证模型
"""
from __future__ import annotations

from datetime import date as DateType
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .notice import NoticeResponse
from .resource import ResourceListItemResponse


class TrainingScheduleItem(BaseModel):
    """课程排课条目"""

    session_id: Optional[str] = None
    date: DateType
    time_range: str
    hours: Optional[float] = 0
    location: Optional[str] = None
    status: str = "pending"
    started_at: Optional[datetime] = None
    checkin_started_at: Optional[datetime] = None
    checkin_ended_at: Optional[datetime] = None
    checkout_started_at: Optional[datetime] = None
    checkout_ended_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    skipped_by: Optional[int] = None
    skip_reason: Optional[str] = None
    is_expired: bool = False
    can_edit: bool = False
    can_delete: bool = False


class TrainingSessionActionPermissions(BaseModel):
    """课次可执行操作"""

    can_start_checkin: bool = False
    can_end_checkin: bool = False
    can_start_checkout: bool = False
    can_end_checkout: bool = False
    can_skip: bool = False


class TrainingCurrentSessionResponse(BaseModel):
    """当前课次摘要"""

    course_id: int
    course_name: str
    session_id: str
    session_label: str
    date: DateType
    time_range: str
    status: str
    location: Optional[str] = None
    primary_instructor_id: Optional[int] = None
    primary_instructor_name: Optional[str] = None
    assistant_instructor_ids: List[int] = Field(default_factory=list)
    assistant_instructor_names: List[str] = Field(default_factory=list)
    action_permissions: TrainingSessionActionPermissions = Field(default_factory=TrainingSessionActionPermissions)


class TrainingCourseCreate(BaseModel):
    """创建培训课程安排"""

    course_key: Optional[str] = Field(None, description="稳定课程键")
    name: str = Field(..., max_length=200, description="课程名称")
    location: Optional[str] = Field(None, max_length=200, description="课程地点")
    instructor: Optional[str] = Field(None, description="主讲教官名称")
    primary_instructor_id: Optional[int] = Field(None, description="主讲教官ID")
    assistant_instructor_ids: List[int] = Field(default_factory=list, description="带教教官ID列表")
    hours: float = Field(0, description="课时")
    type: str = Field("theory", description="类型: theory/practice")
    schedules: List[TrainingScheduleItem] = Field(default_factory=list)


class TrainingCourseResponse(BaseModel):
    """培训课程安排响应"""

    id: int
    training_id: int
    course_key: Optional[str] = None
    name: str
    location: Optional[str] = None
    instructor: Optional[str] = None
    primary_instructor_id: Optional[int] = None
    primary_instructor_name: Optional[str] = None
    assistant_instructor_ids: List[int] = Field(default_factory=list)
    assistant_instructor_names: List[str] = Field(default_factory=list)
    hours: float = 0
    type: str = "theory"
    schedules: List[TrainingScheduleItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TrainingExamSummary(BaseModel):
    """培训班内考试摘要"""

    id: int
    title: str
    purpose: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    question_count: int = 0
    passing_score: int = 60


class TrainingBaseCreate(BaseModel):
    """创建培训基地"""

    name: str = Field(..., max_length=200, description="培训基地名称")
    location: str = Field(..., max_length=200, description="培训基地地点")
    department_id: Optional[int] = Field(None, description="部门ID")
    description: Optional[str] = Field(None, description="备注")


class TrainingBaseUpdate(BaseModel):
    """更新培训基地"""

    name: Optional[str] = Field(None, max_length=200, description="培训基地名称")
    location: Optional[str] = Field(None, max_length=200, description="培训基地地点")
    department_id: Optional[int] = Field(None, description="部门ID")
    description: Optional[str] = Field(None, description="备注")


class TrainingBaseResponse(BaseModel):
    """培训基地响应"""

    id: int
    name: str
    location: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    created_by: Optional[int] = None
    description: Optional[str] = None
    linked_training_count: int = 0
    upcoming_training_count: int = 0
    active_training_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingWorkflowStepResponse(BaseModel):
    """培训班步骤条节点"""

    key: str
    title: str
    status: str
    description: Optional[str] = None


class TrainingWorkflowActionRequest(BaseModel):
    """培训班流程动作请求"""

    skip_steps: List[str] = Field(default_factory=list, description="允许跳过的前置流程节点")


class TrainingCreate(BaseModel):
    """创建培训班"""

    name: str = Field(..., max_length=200, description="培训名称")
    type: str = Field(..., description="培训类型: basic/special/promotion/online")
    status: str = Field("upcoming", description="状态")
    publish_status: str = Field("draft", description="发布状态")
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = Field(None, max_length=200)
    department_id: Optional[int] = None
    police_type_id: Optional[int] = None
    training_base_id: Optional[int] = None
    class_code: Optional[str] = Field(None, max_length=100)
    instructor_id: Optional[int] = None
    capacity: int = Field(0, description="容量")
    description: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    enrollment_requires_approval: bool = Field(True, description="报名是否需要审核")
    enrollment_start_at: Optional[datetime] = None
    enrollment_end_at: Optional[datetime] = None
    admission_exam_id: Optional[int] = None
    courses: List[TrainingCourseCreate] = Field(default_factory=list)


class TrainingRosterAssignment(BaseModel):
    """学员编组和班干部设置"""

    enrollment_id: int
    group_name: Optional[str] = Field(None, max_length=100)
    cadre_role: Optional[str] = Field(None, max_length=100)


class TrainingUpdate(BaseModel):
    """更新培训班"""

    name: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = None
    status: Optional[str] = None
    publish_status: Optional[str] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    police_type_id: Optional[int] = None
    training_base_id: Optional[int] = None
    class_code: Optional[str] = None
    instructor_id: Optional[int] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    subjects: Optional[List[str]] = None
    enrollment_requires_approval: Optional[bool] = None
    enrollment_start_at: Optional[datetime] = None
    enrollment_end_at: Optional[datetime] = None
    admission_exam_id: Optional[int] = None
    courses: Optional[List[TrainingCourseCreate]] = None
    student_ids: Optional[List[int]] = None
    roster_assignments: Optional[List[TrainingRosterAssignment]] = None


class TrainingResponse(BaseModel):
    """培训班响应"""

    id: int
    name: str
    type: str
    status: str = "upcoming"
    publish_status: str = "draft"
    progress_percent: int = 0
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    training_base_id: Optional[int] = None
    training_base_name: Optional[str] = None
    created_by: Optional[int] = None
    class_code: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    capacity: int = 0
    enrolled_count: int = 0
    student_ids: List[int] = Field(default_factory=list)
    students: List["EnrollmentResponse"] = Field(default_factory=list)
    description: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    enrollment_requires_approval: bool = True
    enrollment_start_at: Optional[datetime] = None
    enrollment_end_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    is_locked: bool = False
    admission_exam_id: Optional[int] = None
    admission_exam_title: Optional[str] = None
    group_names: List[str] = Field(default_factory=list)
    cadre_count: int = 0
    courses: List[TrainingCourseResponse] = Field(default_factory=list)
    exam_sessions: List[TrainingExamSummary] = Field(default_factory=list)
    checkin_records: List["CheckinResponse"] = Field(default_factory=list)
    notices: List[NoticeResponse] = Field(default_factory=list)
    resources: List[ResourceListItemResponse] = Field(default_factory=list)
    workflow_steps: List[TrainingWorkflowStepResponse] = Field(default_factory=list)
    current_step_key: str = "draft"
    current_session: Optional[TrainingCurrentSessionResponse] = None
    can_manage_all: bool = False
    can_manage_training: bool = False
    can_edit_training: bool = False
    can_edit_courses: bool = False
    can_view_course_change_logs: bool = False
    can_review_enrollments: bool = False
    current_enrollment_status: Optional[str] = None
    can_enter_training: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingListResponse(BaseModel):
    """培训班列表响应"""

    id: int
    name: str
    type: str
    status: str = "upcoming"
    publish_status: str = "draft"
    progress_percent: int = 0
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    training_base_id: Optional[int] = None
    training_base_name: Optional[str] = None
    created_by: Optional[int] = None
    class_code: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    capacity: int = 0
    enrolled_count: int = 0
    student_ids: List[int] = Field(default_factory=list)
    description: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    enrollment_requires_approval: bool = True
    enrollment_start_at: Optional[datetime] = None
    enrollment_end_at: Optional[datetime] = None
    is_locked: bool = False
    admission_exam_id: Optional[int] = None
    admission_exam_title: Optional[str] = None
    current_step_key: str = "draft"
    current_enrollment_status: Optional[str] = None
    can_enter_training: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    """报名"""

    note: Optional[str] = Field(None, description="报名备注")
    phone: Optional[str] = Field(None, description="联系电话")
    need_accommodation: bool = Field(False, description="是否需要住宿")


class EnrollmentResponse(BaseModel):
    """报名响应"""

    id: int
    training_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    police_id: Optional[str] = None
    departments: List[str] = Field(default_factory=list)
    status: str = "pending"
    note: Optional[str] = None
    contact_phone: Optional[str] = None
    need_accommodation: bool = False
    group_name: Optional[str] = None
    cadre_role: Optional[str] = None
    approved_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    enroll_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CheckinCreate(BaseModel):
    """签到"""

    date: Optional[DateType] = None
    time: Optional[str] = Field(None, description="签到时间 HH:MM")
    session_key: str = Field("start", description="课次标识")
    user_id: Optional[int] = None
    status: Optional[str] = Field(None, description="签到状态，默认自动判断")


class CheckoutCreate(BaseModel):
    """签退"""

    date: Optional[DateType] = None
    time: Optional[str] = Field(None, description="签退时间 HH:MM")
    session_key: str = Field("start", description="课次标识")
    user_id: Optional[int] = None


class TrainingEvaluationCreate(BaseModel):
    """评课"""

    date: Optional[DateType] = None
    session_key: str = Field("start", description="课次标识")
    user_id: Optional[int] = None
    score: int = Field(..., ge=1, le=5, description="评分")
    comment: Optional[str] = Field(None, max_length=500, description="评语")


class TrainingSkipCourseRequest(BaseModel):
    """跳过课程"""

    reason: Optional[str] = Field(None, max_length=200, description="跳过原因")


class CheckinResponse(BaseModel):
    """签到响应"""

    id: int
    training_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    date: Optional[DateType] = None
    time: Optional[str] = None
    status: str = "on_time"
    session_key: str = "start"
    checkout_time: Optional[str] = None
    checkout_status: str = "pending"
    evaluation_score: Optional[int] = None
    evaluation_comment: Optional[str] = None
    evaluation_submitted_at: Optional[datetime] = None
    absence_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingAttendanceSummaryResponse(BaseModel):
    """签到汇总"""

    session_key: str
    total_students: int
    on_time_count: int
    late_count: int
    absent_count: int
    checked_out_count: int
    evaluated_count: int
    completion_rate: int
    session_status: Optional[str] = None


class TrainingCheckinQrResponse(BaseModel):
    """签到二维码响应"""

    token: str
    training_id: int
    training_name: str
    session_key: str
    session_label: str
    date: Optional[DateType] = None
    url: str
    expire_at: datetime
    expires_in_seconds: int


class ScheduleItemCreate(BaseModel):
    """创建计划条目"""

    week_start: Optional[DateType] = None
    day: Optional[int] = Field(None, ge=1, le=7)
    date: Optional[DateType] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    title: str = Field(..., max_length=200)
    type: str = Field("theory", description="类型")
    location: Optional[str] = None
    instructor: Optional[str] = None
    participants: Optional[str] = None
    content: Optional[str] = None
    status: str = Field("pending", description="状态")


class ScheduleItemResponse(BaseModel):
    """计划条目响应"""

    id: int
    training_id: int
    week_start: Optional[DateType] = None
    day: Optional[int] = None
    date: Optional[DateType] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    title: str
    type: str = "theory"
    location: Optional[str] = None
    instructor: Optional[str] = None
    participants: Optional[str] = None
    content: Optional[str] = None
    status: str = "pending"

    model_config = ConfigDict(from_attributes=True)


class TrainingHistoryResponse(BaseModel):
    """训历响应"""

    id: int
    training_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    police_id: Optional[str] = None
    departments: List[str] = Field(default_factory=list)
    training_name: str
    training_type: str
    status: str
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    attendance_rate: float = 0
    completed_sessions: int = 0
    total_sessions: int = 0
    evaluation_score: float = 0
    passed_exam_count: int = 0
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingCourseChangeLogResponse(BaseModel):
    """培训班课程变更记录响应"""

    id: int
    training_id: int
    course_key: Optional[str] = None
    session_key: Optional[str] = None
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    target_type: str
    action: str
    source: str
    batch_id: str
    course_name: Optional[str] = None
    session_label: Optional[str] = None
    summary: Optional[str] = None
    before_json: Optional[dict] = None
    after_json: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
