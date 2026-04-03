"""
控制器导出
"""
from .user import UserController
from .role import RoleController
from .permission import PermissionController
from .department import DepartmentController
from .police_type import PoliceTypeController
from .training_type import TrainingTypeController
from .knowledge_point import KnowledgePointController
from .system import SystemConfigController
from .course import CourseController
from .exam import ExamController
from .question import QuestionController
from .training import TrainingController
from .training_base import TrainingBaseController
from .certificate import CertificateController
from .profile import ProfileController
from .dashboard import DashboardController
from .report import ReportController
from .ai import AIController
from .talent import TalentController
from .media import MediaController
from .resource import ResourceController
from .library import LibraryController
from .resource_comment import ResourceCommentController
from .review import ReviewController
from .recommendation import RecommendationController

__all__ = [
    "UserController",
    "RoleController",
    "PermissionController",
    "DepartmentController",
    "PoliceTypeController",
    "TrainingTypeController",
    "KnowledgePointController",
    "SystemConfigController",
    "CourseController",
    "ExamController",
    "QuestionController",
    "TrainingController",
    "TrainingBaseController",
    "CertificateController",
    "ProfileController",
    "DashboardController",
    "ReportController",
    "AIController",
    "TalentController",
    "MediaController",
    "ResourceController",
    "LibraryController",
    "ResourceCommentController",
    "ReviewController",
    "RecommendationController",
]
