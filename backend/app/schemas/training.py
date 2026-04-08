"""
培训管理相关的数据验证模型
"""

from datetime import date as DateType
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .notice import NoticeResponse
from .resource import ResourceListItemResponse


class TrainingScheduleRuleWindow(BaseModel):
    """培训班排课时间窗口"""

    label: Optional[str] = Field(None, max_length=50, description="时间段标签")
    start_time: str = Field(..., description="开始时间 HH:MM")
    end_time: str = Field(..., description="结束时间 HH:MM")


class TrainingScheduleRuleConfig(BaseModel):
    """培训班排课规则配置"""

    lesson_unit_minutes: int = Field(40, ge=20, le=180, description="单课时分钟数")
    break_minutes: int = Field(10, ge=0, le=60, description="课间休息分钟数")
    max_units_per_session: int = Field(3, ge=1, le=12, description="单节最多课时")
    daily_max_units: int = Field(6, ge=1, le=24, description="单日最多课时")
    preferred_planning_mode: str = Field("fill_workdays", description="默认排课方式")
    split_strategy: str = Field("balanced", description="拆分策略")
    teaching_windows: List[TrainingScheduleRuleWindow] = Field(default_factory=list, description="可排课时间段")


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
    edit_lock_reason: Optional[str] = None
    edit_lock_message: Optional[str] = None
    delete_lock_message: Optional[str] = None


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
    checkin_mode: Optional[str] = None  # "direct" or "qr"
    checkin_duration_minutes: Optional[int] = None
    checkin_deadline: Optional[str] = None  # ISO datetime
    checkout_mode: Optional[str] = None  # "direct" or "qr"
    checkout_duration_minutes: Optional[int] = None
    checkout_deadline: Optional[str] = None  # ISO datetime
    checkin_gesture_pattern: Optional[str] = None  # JSON array string like "[0,1,2,5,8]"
    checkout_gesture_pattern: Optional[str] = None
    action_permissions: TrainingSessionActionPermissions = Field(default_factory=TrainingSessionActionPermissions)


class TrainingCourseCreate(BaseModel):
    """创建培训课程安排"""

    course_id: Optional[int] = Field(None, description="关联课程资源ID（为空则是自定义课程）")
    course_key: Optional[str] = Field(None, description="稳定课程键")
    name: str = Field("", max_length=200, description="课程名称（绑定课程资源时可不填，自动从资源取）")
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
    course_id: Optional[int] = None
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


class CourseResourceItem(BaseModel):
    """课程资源摘要（用于培训班课程选择）"""

    id: int
    title: str
    category: Optional[str] = None
    file_type: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    duration: Optional[int] = None
    chapter_count: int = 0

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
    capacity: Optional[int] = Field(None, description="最大容纳人数")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    area_size: Optional[str] = Field(None, max_length=50, description="占地面积")
    facilities: Optional[str] = Field(None, max_length=500, description="设施设备描述")
    status: Optional[str] = Field("active", description="状态: active/inactive")
    description: Optional[str] = Field(None, description="备注")


class TrainingBaseUpdate(BaseModel):
    """更新培训基地"""

    name: Optional[str] = Field(None, max_length=200, description="培训基地名称")
    location: Optional[str] = Field(None, max_length=200, description="培训基地地点")
    department_id: Optional[int] = Field(None, description="部门ID")
    capacity: Optional[int] = Field(None, description="最大容纳人数")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    area_size: Optional[str] = Field(None, max_length=50, description="占地面积")
    facilities: Optional[str] = Field(None, max_length=500, description="设施设备描述")
    status: Optional[str] = Field(None, description="状态: active/inactive")
    description: Optional[str] = Field(None, description="备注")


class TrainingBaseResponse(BaseModel):
    """培训基地响应"""

    id: int
    name: str
    location: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    created_by: Optional[int] = None
    capacity: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    area_size: Optional[str] = None
    facilities: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    used_capacity: int = 0
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
    training_type_id: Optional[int] = Field(None, description="培训班类型ID，不传时根据 type 自动匹配")
    status: str = Field("upcoming", description="状态")
    publish_status: str = Field("draft", description="发布状态")
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = Field(None, max_length=200)
    department_id: Optional[int] = None
    visibility_scope: str = Field("all", description="可见范围: all/department/department_and_sub")
    visibility_department_ids: Optional[List[int]] = Field(None, description="可见部门ID列表")
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
    schedule_rule_config: Optional[TrainingScheduleRuleConfig] = Field(None, description="排课规则配置")
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
    visibility_scope: Optional[str] = Field(None, description="可见范围: all/department/department_and_sub")
    visibility_department_ids: Optional[List[int]] = Field(None, description="可见部门ID列表")
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
    schedule_rule_config: Optional[TrainingScheduleRuleConfig] = Field(None, description="排课规则配置")
    courses: Optional[List[TrainingCourseCreate]] = None
    student_ids: Optional[List[int]] = None
    roster_assignments: Optional[List[TrainingRosterAssignment]] = None


# ========== Enrollment / Checkin (定义在 TrainingResponse 之前以避免 forward reference) ==========

class EnrollmentCreate(BaseModel):
    """报名"""

    note: Optional[str] = Field(None, description="报名备注")
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
    checkin_rate: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CheckinCreate(BaseModel):
    """签到"""

    date: Optional[DateType] = None
    time: Optional[str] = Field(None, description="签到时间 HH:MM")
    session_key: str = Field("start", description="课次标识")
    user_id: Optional[int] = None
    status: Optional[str] = Field(None, description="签到状态，默认自动判断")
    method: Optional[str] = Field(None, description="签到方式: direct/qr/manual，默认自动判断")


class CheckoutCreate(BaseModel):
    """签退"""

    date: Optional[DateType] = None
    time: Optional[str] = Field(None, description="签退时间 HH:MM")
    session_key: str = Field("start", description="课次标识")
    user_id: Optional[int] = None
    method: Optional[str] = Field(None, description="签退方式: direct/qr/manual，默认自动判断")


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


class BatchManualCheckinItem(BaseModel):
    """批量手动签到单条"""

    user_id: int
    status: str = Field("on_time", description="on_time / late / absent")
    absence_reason: Optional[str] = Field(None, max_length=200, description="缺勤原因")


class BatchManualCheckinRequest(BaseModel):
    """批量手动签到请求"""

    session_key: str = Field(..., description="课次标识")
    items: List[BatchManualCheckinItem] = Field(..., min_length=1)


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


class TrainingActivityResponse(BaseModel):
    """培训班动态响应"""

    id: int
    training_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action_type: str
    content: str
    extra_json: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


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
    visibility_scope: str = "all"
    visibility_department_ids: Optional[List[int]] = None
    visibility_department_names: Optional[List[str]] = None
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    training_type_id: Optional[int] = None
    training_type_name: Optional[str] = None
    training_base_id: Optional[int] = None
    training_base_name: Optional[str] = None
    created_by: Optional[int] = None
    class_code: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    capacity: int = 0
    enrolled_count: int = 0
    student_ids: List[int] = Field(default_factory=list)
    students: List[EnrollmentResponse] = Field(default_factory=list)
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
    schedule_rule_config: TrainingScheduleRuleConfig = Field(default_factory=TrainingScheduleRuleConfig)
    courses: List[TrainingCourseResponse] = Field(default_factory=list)
    exam_sessions: List[TrainingExamSummary] = Field(default_factory=list)
    checkin_records: List[CheckinResponse] = Field(default_factory=list)
    notices: List[NoticeResponse] = Field(default_factory=list)
    resources: List[ResourceListItemResponse] = Field(default_factory=list)
    workflow_steps: List[TrainingWorkflowStepResponse] = Field(default_factory=list)
    current_step_key: str = "draft"
    current_session: Optional[TrainingCurrentSessionResponse] = None
    recent_activities: List[TrainingActivityResponse] = Field(default_factory=list)
    is_related_user: bool = False
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
    visibility_scope: str = "all"
    visibility_department_ids: Optional[List[int]] = None
    visibility_department_names: Optional[List[str]] = None
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    training_type_id: Optional[int] = None
    training_type_name: Optional[str] = None
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


class TrainingStatsResponse(BaseModel):
    """培训班统计响应"""

    total: int = 0
    published: int = 0
    active: int = 0
    locked: int = 0


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
    """出勤二维码响应"""

    token: str
    training_id: int
    training_name: str
    session_key: str
    session_label: str
    date: Optional[DateType] = None
    url: str
    expire_at: datetime
    expires_in_seconds: int
    action: str = Field("checkin", description="出勤动作: checkin/checkout")


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


class CalendarEventResponse(BaseModel):
    """聚合日历事件（跨班级合并课时）"""

    training_id: int
    training_name: str
    course_name: str
    course_type: str = "theory"
    date: DateType
    time_range: str
    hours: Optional[float] = 0
    location: Optional[str] = None
    instructor: Optional[str] = None
    status: str = "pending"
    session_id: Optional[str] = None


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
