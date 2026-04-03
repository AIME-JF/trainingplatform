"""
智能解析课表文件 - 数据验证模型
"""
from datetime import date as DateType, datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# 子结构
# ---------------------------------------------------------------------------

class ScheduleFileHeadteacher(BaseModel):
    """班主任信息"""

    name: str = Field(..., max_length=100, description="姓名")
    role_label: Optional[str] = Field(None, max_length=50, description="称呼，如带班队长/带班教官")
    user_id: Optional[int] = Field(None, description="匹配到的用户 ID")
    auto_create: bool = Field(False, description="是否需要自动创建账号")


class ScheduleFileInstructor(BaseModel):
    """课程教官信息"""

    name: Optional[str] = Field(None, max_length=100, description="姓名，组织/形式则为 null")
    user_id: Optional[int] = Field(None, description="匹配到的用户 ID")
    auto_create: bool = Field(False, description="是否需要自动创建账号")


class ScheduleFileCourseSession(BaseModel):
    """课次"""

    date: str = Field(..., description="日期 YYYY-MM-DD")
    time_start: str = Field(..., description="开始时间 HH:MM")
    time_end: str = Field(..., description="结束时间 HH:MM")
    location: Optional[str] = Field(None, max_length=200, description="地点")


class ScheduleFileCourse(BaseModel):
    """解析后的课程"""

    name: str = Field(..., max_length=200, description="课程名称")
    type: Literal["theory", "practice"] = Field("theory", description="课程类型")
    location: Optional[str] = Field(None, max_length=200, description="课程默认地点")
    primary_instructor: ScheduleFileInstructor = Field(default_factory=ScheduleFileInstructor, description="主讲教官")
    assistant_instructors: List[ScheduleFileInstructor] = Field(default_factory=list, description="辅助教官")
    sessions: List[ScheduleFileCourseSession] = Field(default_factory=list, description="课次列表")


class ScheduleFileClassInfo(BaseModel):
    """班级信息"""

    name: Optional[str] = Field(None, max_length=200, description="班级名称")
    start_date: Optional[str] = Field(None, description="起始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    capacity: Optional[int] = Field(None, ge=1, le=9999, description="班级容量")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    location_source: Literal["base", "manual"] = Field("manual", description="地点来源: base=培训基地 / manual=手动输入")
    training_base_id: Optional[int] = Field(None, description="匹配到的培训基地 ID")
    headteachers: List[ScheduleFileHeadteacher] = Field(default_factory=list, description="班主任列表")


class ScheduleFileTrainingConfig(BaseModel):
    """步骤4 完善的培训班配置"""

    type: str = Field("basic", description="培训类型: basic/special/promotion/online")
    department_id: Optional[int] = Field(None, description="所属部门 ID")
    police_type_id: Optional[int] = Field(None, description="警种 ID")
    visibility_scope: str = Field("all", description="可见范围: all/department/department_and_sub")
    visibility_department_ids: Optional[List[int]] = Field(None, description="可见部门 ID 列表")
    description: Optional[str] = Field(None, description="培训简介")
    enrollment_requires_approval: bool = Field(True, description="报名是否需要审核")
    admission_exam_id: Optional[int] = Field(None, description="准入考试 ID")
    enrollment_start_at: Optional[datetime] = Field(None, description="报名开始时间")
    enrollment_end_at: Optional[datetime] = Field(None, description="报名结束时间")
    class_code: Optional[str] = Field(None, max_length=100, description="班级编号")


# ---------------------------------------------------------------------------
# 任务阶段
# ---------------------------------------------------------------------------

ScheduleFileParseTaskStage = Literal[
    "parsing",
    "class_info_confirmation",
    "course_confirmation",
    "training_config",
    "preview",
    "confirmed",
]


# ---------------------------------------------------------------------------
# API 请求 / 响应
# ---------------------------------------------------------------------------

class ScheduleFileParseTaskUpdateRequest(BaseModel):
    """智能解析课表任务更新请求（步骤 2-4 提交）"""

    task_name: Optional[str] = Field(None, max_length=200, description="任务名称")
    confirmed_class_info: Optional[ScheduleFileClassInfo] = Field(None, description="确认后的班级信息")
    confirmed_courses: Optional[List[ScheduleFileCourse]] = Field(None, description="确认后的课程列表")
    training_config: Optional[ScheduleFileTrainingConfig] = Field(None, description="完善的培训班配置")
    current_stage: Optional[ScheduleFileParseTaskStage] = Field(None, description="当前提交阶段")


class ScheduleFileParseTaskDetailResponse(BaseModel):
    """智能解析课表任务详情响应"""

    id: int
    task_name: str
    task_type: str
    status: str
    task_stage: Optional[str] = None
    created_by: int
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    can_delete: bool = False
    error_message: Optional[str] = None

    # 请求信息
    file_name: Optional[str] = None

    # Agent 解析结果
    class_info: Optional[ScheduleFileClassInfo] = None
    courses: List[ScheduleFileCourse] = Field(default_factory=list)
    parse_success: bool = False
    parse_error: Optional[str] = None

    # 用户确认数据
    confirmed_class_info: Optional[ScheduleFileClassInfo] = None
    confirmed_courses: Optional[List[ScheduleFileCourse]] = None
    training_config: Optional[ScheduleFileTrainingConfig] = None

    # 确认结果
    confirmed_training_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
