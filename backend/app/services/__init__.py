"""
服务层导出
"""
from .auth import AuthService
from .user import UserService
from .department import DepartmentService
from .role import RoleService
from .permission import PermissionService
from .police_type import PoliceTypeService
from .training_type import TrainingTypeService
from .knowledge_point import KnowledgePointService
from .system import SystemConfigService
from .course import CourseService
from .course_progress import CourseProgressService
from .exam import ExamService
from .question import QuestionService
from .training import TrainingService
from .training_course_change import TrainingCourseChangeService
from .training_base import TrainingBaseService
from .certificate import CertificateService
from .profile import ProfileService
from .dashboard import DashboardService
from .report import ReportService
from .ai import AIService
from .teaching_resource_generation import TeachingResourceGenerationService
from .training_portrait_aggregator import TrainingPortraitAggregator
from .training_ai import TrainingAIService
from .talent import TalentService
from .media import MediaService
from .notice import NoticeService
from .resource import ResourceService
from .review import ReviewService
from .recommendation import RecommendationService
from .schedule_file_parse import ScheduleFileParseService
from .knowledge_base import KnowledgeBaseService
from .knowledge_chat import KnowledgeChatService
from .scenario import ScenarioService

__all__ = [
    "AuthService", "UserService", "DepartmentService", "RoleService", "PermissionService",
    "PoliceTypeService", "TrainingTypeService", "KnowledgePointService", "SystemConfigService",
    "CourseService", "CourseProgressService", "ExamService", "QuestionService", "TrainingService",
    "TrainingCourseChangeService", "TrainingBaseService",
    "CertificateService", "ProfileService",
    "DashboardService", "ReportService", "AIService", "TeachingResourceGenerationService",
    "TrainingPortraitAggregator", "TrainingAIService", "TalentService",
    "MediaService", "NoticeService",
    "ResourceService", "ReviewService", "RecommendationService", "ScheduleFileParseService",
    "KnowledgeBaseService", "KnowledgeChatService", "ScenarioService",
]
