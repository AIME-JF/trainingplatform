"""
Pydantic模型导出
"""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserSimpleResponse, UserLogin, LoginResponse,
    PasswordChange, TokenData, UserRoleUpdate, UserDepartmentUpdate, UserPoliceTypeUpdate
)
from .role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleSimpleResponse,
    RolePermissionUpdate
)
from .permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse
)
from .department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentSimpleResponse,
    DepartmentPermissionUpdate
)
from .police_type import (
    PoliceTypeCreate, PoliceTypeUpdate, PoliceTypeResponse, PoliceTypeSimpleResponse
)
from .system import (
    ConfigCreate, ConfigUpdate, ConfigResponse,
    ConfigGroupCreate, ConfigGroupUpdate, ConfigGroupResponse, ConfigGroupDetailResponse,
    PublicConfigResponse
)
from .response import StandardResponse, PaginatedResponse

# 课程相关
from .course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    ChapterCreate, ChapterUpdate, ChapterResponse,
    CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse,
    CourseQACreate, CourseQAResponse
)
# 培训相关
from .training import (
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    TrainingCourseCreate, TrainingCourseResponse,
    EnrollmentCreate, EnrollmentResponse,
    CheckinCreate, CheckinResponse,
    ScheduleItemCreate, ScheduleItemResponse
)
# 考试相关
from .exam import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate,
    ExamCreate, ExamUpdate, ExamResponse, ExamDetailResponse, ExamQuestionResponse,
    ExamSubmit, ExamRecordResponse
)
# 证书相关
from .certificate import CertificateCreate, CertificateResponse
# 个人中心
from .profile import ProfileUpdate, ProfileResponse, StudyStatsResponse, ExamHistoryResponse
# 工作台
from .dashboard import DashboardResponse
# 数据看板
from .report import (
    KpiResponse, TrendItem, PoliceTypeDistribution, CityRanking,
    TrainingTrendItem, CityAttendanceItem, CityCompletionItem
)
# AI功能
from .ai import (
    AIGenerateQuestionsRequest, AIGenerateQuestionsResponse,
    AIGenerateLessonPlanRequest, AIGenerateLessonPlanResponse
)
# 人才库
from .talent import TalentResponse, TalentStatsResponse
# 文件管理
from .media import MediaFileResponse
# 公告
from .notice import NoticeCreate, NoticeUpdate, NoticeResponse
from .resource import (
    ResourceCreate, ResourceUpdate,
    ResourceMediaLinkPayload, ResourceMediaLinkResponse,
    ResourceListItemResponse, ResourceDetailResponse,
    CourseResourceBindRequest, TrainingResourceBindRequest
)
from .review import (
    ReviewPolicyCreate, ReviewPolicyUpdate,
    ReviewPolicyResponse, ReviewPolicyStageResponse,
    ReviewTaskActionRequest, ReviewTaskResponse,
    ReviewWorkflowResponse
)
from .recommendation import (
    ResourceBehaviorEventCreate,
    ResourceRecommendationItem, ResourceRecommendationFeedResponse,
    RecommendationScoreBreakdown
)


__all__ = [
    # 用户相关
    "UserCreate", "UserUpdate", "UserResponse", "UserSimpleResponse", "UserLogin", "LoginResponse",
    "PasswordChange", "TokenData", "UserRoleUpdate", "UserDepartmentUpdate", "UserPoliceTypeUpdate",
    # 角色相关
    "RoleCreate", "RoleUpdate", "RoleResponse", "RoleSimpleResponse",
    "RolePermissionUpdate",
    # 权限相关
    "PermissionCreate", "PermissionUpdate", "PermissionResponse",
    # 部门相关
    "DepartmentCreate", "DepartmentUpdate", "DepartmentResponse",
    "DepartmentSimpleResponse", "DepartmentPermissionUpdate",
    # 警种相关
    "PoliceTypeCreate", "PoliceTypeUpdate", "PoliceTypeResponse", "PoliceTypeSimpleResponse",
    # 系统配置相关
    "ConfigCreate", "ConfigUpdate", "ConfigResponse",
    "ConfigGroupCreate", "ConfigGroupUpdate", "ConfigGroupResponse", "ConfigGroupDetailResponse",
    "PublicConfigResponse",
    # 响应相关
    "StandardResponse", "PaginatedResponse",
    # 课程相关
    "CourseCreate", "CourseUpdate", "CourseResponse", "CourseListResponse",
    "ChapterCreate", "ChapterUpdate", "ChapterResponse",
    "CourseProgressUpdate", "CourseProgressResponse", "CourseNoteUpdate", "CourseNoteResponse",
    "CourseQACreate", "CourseQAResponse",
    # 培训相关
    "TrainingCreate", "TrainingUpdate", "TrainingResponse", "TrainingListResponse",
    "TrainingCourseCreate", "TrainingCourseResponse",
    "EnrollmentCreate", "EnrollmentResponse",
    "CheckinCreate", "CheckinResponse",
    "ScheduleItemCreate", "ScheduleItemResponse",
    # 考试相关
    "QuestionCreate", "QuestionUpdate", "QuestionResponse", "QuestionBatchCreate",
    "ExamCreate", "ExamUpdate", "ExamResponse", "ExamDetailResponse", "ExamQuestionResponse",
    "ExamSubmit", "ExamRecordResponse",
    # 证书相关
    "CertificateCreate", "CertificateResponse",
    # 个人中心
    "ProfileUpdate", "ProfileResponse", "StudyStatsResponse", "ExamHistoryResponse",
    # 工作台
    "DashboardResponse",
    # 数据看板
    "KpiResponse", "TrendItem", "PoliceTypeDistribution", "CityRanking",
    "TrainingTrendItem", "CityAttendanceItem", "CityCompletionItem",
    # AI功能
    "AIGenerateQuestionsRequest", "AIGenerateQuestionsResponse",
    "AIGenerateLessonPlanRequest", "AIGenerateLessonPlanResponse",
    # 人才库
    "TalentResponse", "TalentStatsResponse",
    # 文件管理
    "MediaFileResponse",
    # 公告
    "NoticeCreate", "NoticeUpdate", "NoticeResponse",
    # 资源库
    "ResourceCreate", "ResourceUpdate",
    "ResourceMediaLinkPayload", "ResourceMediaLinkResponse",
    "ResourceListItemResponse", "ResourceDetailResponse",
    "CourseResourceBindRequest", "TrainingResourceBindRequest",
    # 审核
    "ReviewPolicyCreate", "ReviewPolicyUpdate",
    "ReviewPolicyResponse", "ReviewPolicyStageResponse",
    "ReviewTaskActionRequest", "ReviewTaskResponse", "ReviewWorkflowResponse",
    # 推荐
    "ResourceBehaviorEventCreate",
    "ResourceRecommendationItem", "ResourceRecommendationFeedResponse",
    "RecommendationScoreBreakdown",
]
