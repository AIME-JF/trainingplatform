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
from .training_type import (
    TrainingTypeCreate, TrainingTypeUpdate, TrainingTypeResponse
)
from .knowledge_point import (
    KnowledgePointCreate, KnowledgePointUpdate, KnowledgePointResponse, KnowledgePointSimpleResponse
)
from .system import (
    ConfigCreate, ConfigUpdate, ConfigResponse,
    ConfigGroupCreate, ConfigGroupUpdate, ConfigGroupResponse, ConfigGroupDetailResponse,
    PublicConfigResponse,
    DashboardModuleConfigCreate, DashboardModuleConfigUpdate, DashboardModuleConfigResponse,
)
from .response import StandardResponse, PaginatedResponse

# 课程相关
from .course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    ChapterCreate, ChapterUpdate, ChapterResponse,
    CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse,
    CourseQACreate, CourseQAResponse,
    CourseTagCreate, CourseTagResponse, CourseLearningStatusResponse,
    CourseRelatedTrainingResponse,
)
# 培训相关
from .training import (
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    TrainingStatsResponse,
    TrainingBaseCreate, TrainingBaseUpdate, TrainingBaseResponse,
    TrainingCourseCreate, TrainingCourseResponse,
    TrainingScheduleRuleWindow, TrainingScheduleRuleConfig,
    TrainingScheduleItem, TrainingSessionActionPermissions, TrainingCurrentSessionResponse,
    TrainingWorkflowStepResponse, TrainingWorkflowActionRequest, TrainingSkipCourseRequest,
    EnrollmentCreate, EnrollmentResponse,
    TrainingRosterAssignment,
    BatchManualCheckinRequest,
    CheckinCreate, CheckoutCreate, TrainingEvaluationCreate, CheckinResponse,
    TrainingAttendanceSummaryResponse,
    TrainingCheckinQrResponse,
    CalendarEventResponse,
    ScheduleItemCreate, ScheduleItemResponse,
    TrainingExamSummary, TrainingHistoryResponse, TrainingCourseChangeLogResponse,
    TrainingActivityResponse,
)
# 考试相关
from .exam import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate,
    ExamPaperCreate, ExamPaperUpdate, ExamPaperResponse, ExamPaperDetailResponse,
    AdmissionExamCreate, AdmissionExamUpdate, AdmissionExamResponse,
    AdmissionExamDetailResponse, AdmissionExamRecordResponse,
    ExamCreate, ExamUpdate, ExamResponse, ExamDetailResponse,
    ExamSubmit, ExamRecordResponse, ExamQuestionSnapshotResponse,
    ExamParticipantResponse, ExamParticipantImportPreviewResponse,
    ExamParticipantImportConfirmRequest, ExamParticipantImportRowResponse,
    ExamWrongQuestionResponse,
    PaperFolderCreate, PaperFolderUpdate, PaperFolderResponse, PaperMoveRequest,
    QuestionFolderCreate, QuestionFolderUpdate, QuestionFolderResponse, QuestionMoveRequest
)
# 证书相关
from .certificate import CertificateCreate, CertificateResponse
# 个人中心
from .profile import (
    ProfileUpdate, ProfileResponse, StudyStatsResponse,
    ExamHistoryResponse, ProfileOverviewResponse
)
# 工作台
from .dashboard import DashboardResponse
# 数据看板
from .report import (
    KpiResponse, TrendItem, PoliceTypeDistribution, CityRanking,
    TrainingTrendItem, CityAttendanceItem, CityCompletionItem
)
# AI功能
from .ai import (
    AIQuestionTaskCreateRequest, AIQuestionTaskUpdateRequest,
    AIPaperAssemblyParsedRequest, AIPaperAssemblyParsedTypeConfig,
    AIPaperAssemblyTaskCreateRequest, AIPaperAssemblyTypeConfig,
    AIPaperGenerationTaskCreateRequest, AIPaperDocumentGenerationTaskCreateRequest,
    AIPaperTaskUpdateRequest,
    TeachingResourceGenerationTaskCreateRequest, TeachingResourceGenerationParsedRequest,
    TeachingResourceGenerationResourceMeta, TeachingResourceGenerationMetaUpdateRequest,
    TeachingResourceGenerationTemplateSlot, TeachingResourceGenerationTemplatePayload,
    TeachingResourceGenerationPagePlan,
    AIScheduleTaskCreateRequest, AIScheduleTaskConstraintPayload,
    AIScheduleCourseTypeTimePreference, AIScheduleExamWeekFocus,
    AIScheduleTaskStage,
    AIScheduleTaskUpdateRequest, AISchedulePlan, AISchedulePlanMetrics,
    AIScheduleConflictItem, AIScheduleUnavailableSlot,
    AIScheduleParsePreviewResponse,
    AIPersonalTrainingTaskCreateRequest, AIPersonalTrainingTaskUpdateRequest,
    AIPersonalTrainingPortrait, AIPersonalTrainingPortraitTag,
    AIPersonalTrainingPortraitEvidence, AIPersonalTrainingPlan,
    AIPersonalTrainingAction, AIPersonalTrainingResourceRecommendation,
    AITaskQuestionDraft, AITaskPaperDraft, AITaskSummaryResponse,
    AIQuestionTaskDetailResponse, AIPaperAssemblyTaskDetailResponse,
    AIPaperGenerationTaskDetailResponse, AIPaperDocumentGenerationTaskDetailResponse,
    AIScheduleTaskDetailResponse,
    AIPersonalTrainingTaskDetailResponse, TeachingResourceGenerationTaskDetailResponse
)
from .schedule_file_parse import (
    ScheduleFileParseTaskDetailResponse,
    ScheduleFileParseTaskUpdateRequest,
    ScheduleFileClassInfo,
    ScheduleFileCourse,
    ScheduleFileTrainingConfig,
    ScheduleFileHeadteacher,
    ScheduleFileInstructor,
    ScheduleFileCourseSession,
)
# 人才库
from .talent import TalentResponse, TalentStatsResponse
# 文件管理
from .media import MediaFileResponse
# 公告
from .notice import NoticeCreate, NoticeUpdate, NoticeResponse
from .resource import (
    ResourceCreate, ResourceUpdate,
    ResourceTagCreate, ResourceTagResponse,
    ResourceMediaLinkPayload, ResourceMediaLinkResponse,
    ResourceListItemResponse, ResourceDetailResponse, CourseBoundResourceResponse,
    ResourceCommentCreate, ResourceCommentResponse,
    ResourceLikeStatusResponse, ResourceShareStatusResponse,
    CourseResourceBindRequest, TrainingResourceBindRequest, TrainingBoundResourceResponse
)
from .library import (
    LibraryFolderCreate, LibraryFolderUpdate, LibraryFolderResponse,
    LibraryBatchFileCreateRequest, LibraryKnowledgeCreateRequest,
    LibraryItemUpdateRequest, LibraryItemMoveRequest,
    LibraryItemListResponse, LibraryItemDetailResponse, LibraryItemListParams,
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
    # 培训班类型相关
    "TrainingTypeCreate", "TrainingTypeUpdate", "TrainingTypeResponse",
    "KnowledgePointCreate", "KnowledgePointUpdate", "KnowledgePointResponse", "KnowledgePointSimpleResponse",
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
    "CourseQACreate", "CourseQAResponse", "CourseTagCreate", "CourseTagResponse", "CourseLearningStatusResponse",
    "CourseRelatedTrainingResponse",
    # 培训相关
    "TrainingCreate", "TrainingUpdate", "TrainingResponse", "TrainingListResponse", "TrainingStatsResponse",
    "TrainingBaseCreate", "TrainingBaseUpdate", "TrainingBaseResponse",
    "TrainingCourseCreate", "TrainingCourseResponse",
    "TrainingScheduleRuleWindow", "TrainingScheduleRuleConfig",
    "TrainingScheduleItem", "TrainingSessionActionPermissions", "TrainingCurrentSessionResponse",
    "TrainingWorkflowStepResponse", "TrainingWorkflowActionRequest", "TrainingSkipCourseRequest",
    "EnrollmentCreate", "EnrollmentResponse",
    "TrainingRosterAssignment",
    "BatchManualCheckinRequest",
    "CheckinCreate", "CheckoutCreate", "TrainingEvaluationCreate", "CheckinResponse",
    "TrainingAttendanceSummaryResponse", "TrainingCheckinQrResponse",
    "CalendarEventResponse",
    "ScheduleItemCreate", "ScheduleItemResponse",
    "TrainingExamSummary", "TrainingHistoryResponse", "TrainingCourseChangeLogResponse",
    "TrainingActivityResponse",
    # 考试相关
    "QuestionCreate", "QuestionUpdate", "QuestionResponse", "QuestionBatchCreate",
    "ExamPaperCreate", "ExamPaperUpdate", "ExamPaperResponse", "ExamPaperDetailResponse",
    "AdmissionExamCreate", "AdmissionExamUpdate", "AdmissionExamResponse",
    "AdmissionExamDetailResponse", "AdmissionExamRecordResponse",
    "ExamCreate", "ExamUpdate", "ExamResponse", "ExamDetailResponse",
    "ExamSubmit", "ExamRecordResponse", "ExamQuestionSnapshotResponse",
    "ExamParticipantResponse", "ExamParticipantImportPreviewResponse",
    "ExamParticipantImportConfirmRequest", "ExamParticipantImportRowResponse",
    "ExamWrongQuestionResponse",
    "PaperFolderCreate", "PaperFolderUpdate", "PaperFolderResponse", "PaperMoveRequest",
    "QuestionFolderCreate", "QuestionFolderUpdate", "QuestionFolderResponse", "QuestionMoveRequest",
    # 证书相关
    "CertificateCreate", "CertificateResponse",
    # 个人中心
    "ProfileUpdate", "ProfileResponse", "StudyStatsResponse", "ExamHistoryResponse", "ProfileOverviewResponse",
    # 工作台
    "DashboardResponse",
    # 数据看板
    "KpiResponse", "TrendItem", "PoliceTypeDistribution", "CityRanking",
    "TrainingTrendItem", "CityAttendanceItem", "CityCompletionItem",
    # AI功能
    "AIQuestionTaskCreateRequest", "AIQuestionTaskUpdateRequest",
    "AIPaperAssemblyParsedRequest", "AIPaperAssemblyParsedTypeConfig",
    "AIPaperAssemblyTaskCreateRequest", "AIPaperAssemblyTypeConfig",
    "AIPaperGenerationTaskCreateRequest", "AIPaperDocumentGenerationTaskCreateRequest",
    "AIPaperTaskUpdateRequest",
    "TeachingResourceGenerationTaskCreateRequest", "TeachingResourceGenerationParsedRequest",
    "TeachingResourceGenerationResourceMeta", "TeachingResourceGenerationMetaUpdateRequest",
    "TeachingResourceGenerationTemplateSlot", "TeachingResourceGenerationTemplatePayload",
    "TeachingResourceGenerationPagePlan",
    "AIScheduleTaskCreateRequest", "AIScheduleTaskConstraintPayload",
    "AIScheduleCourseTypeTimePreference", "AIScheduleExamWeekFocus",
    "AIScheduleTaskStage",
    "AIScheduleTaskUpdateRequest", "AISchedulePlan", "AISchedulePlanMetrics",
    "AIScheduleConflictItem", "AIScheduleUnavailableSlot",
    "AIScheduleParsePreviewResponse",
    "AIPersonalTrainingTaskCreateRequest", "AIPersonalTrainingTaskUpdateRequest",
    "AIPersonalTrainingPortrait", "AIPersonalTrainingPortraitTag",
    "AIPersonalTrainingPortraitEvidence", "AIPersonalTrainingPlan",
    "AIPersonalTrainingAction", "AIPersonalTrainingResourceRecommendation",
    "AITaskQuestionDraft", "AITaskPaperDraft", "AITaskSummaryResponse",
    "AIQuestionTaskDetailResponse", "AIPaperAssemblyTaskDetailResponse",
    "AIPaperGenerationTaskDetailResponse", "AIPaperDocumentGenerationTaskDetailResponse",
    "AIScheduleTaskDetailResponse",
    "AIPersonalTrainingTaskDetailResponse", "TeachingResourceGenerationTaskDetailResponse",
    # 智能解析课表
    "ScheduleFileParseTaskDetailResponse", "ScheduleFileParseTaskUpdateRequest",
    "ScheduleFileClassInfo", "ScheduleFileCourse", "ScheduleFileTrainingConfig",
    "ScheduleFileHeadteacher", "ScheduleFileInstructor", "ScheduleFileCourseSession",
    # 人才库
    "TalentResponse", "TalentStatsResponse",
    # 文件管理
    "MediaFileResponse",
    # 公告
    "NoticeCreate", "NoticeUpdate", "NoticeResponse",
    # 资源库
    "ResourceCreate", "ResourceUpdate",
    "ResourceTagCreate", "ResourceTagResponse",
    "ResourceMediaLinkPayload", "ResourceMediaLinkResponse",
    "ResourceListItemResponse", "ResourceDetailResponse", "CourseBoundResourceResponse",
    "ResourceCommentCreate", "ResourceCommentResponse",
    "ResourceLikeStatusResponse", "ResourceShareStatusResponse",
    "CourseResourceBindRequest", "TrainingResourceBindRequest",
    # 新资源库
    "LibraryFolderCreate", "LibraryFolderUpdate", "LibraryFolderResponse",
    "LibraryBatchFileCreateRequest", "LibraryKnowledgeCreateRequest",
    "LibraryItemUpdateRequest", "LibraryItemMoveRequest",
    "LibraryItemListResponse", "LibraryItemDetailResponse", "LibraryItemListParams",
    # 审核
    "ReviewPolicyCreate", "ReviewPolicyUpdate",
    "ReviewPolicyResponse", "ReviewPolicyStageResponse",
    "ReviewTaskActionRequest", "ReviewTaskResponse", "ReviewWorkflowResponse",
    # 推荐
    "ResourceBehaviorEventCreate",
    "ResourceRecommendationItem", "ResourceRecommendationFeedResponse",
    "RecommendationScoreBreakdown",
]
