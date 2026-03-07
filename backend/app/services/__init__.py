"""
服务层导出
"""
from .auth import AuthService
from .user import UserService
from .department import DepartmentService
from .role import RoleService
from .permission import PermissionService
from .police_type import PoliceTypeService
from .system import SystemConfigService
from .course import CourseService
from .exam import ExamService
from .question import QuestionService
from .training import TrainingService
from .instructor import InstructorService
from .certificate import CertificateService
from .profile import ProfileService
from .dashboard import DashboardService
from .report import ReportService
from .ai import AIService
from .talent import TalentService
from .media import MediaService

__all__ = [
    "AuthService", "UserService", "DepartmentService", "RoleService", "PermissionService",
    "PoliceTypeService", "SystemConfigService",
    "CourseService", "ExamService", "QuestionService", "TrainingService",
    "InstructorService", "CertificateService", "ProfileService",
    "DashboardService", "ReportService", "AIService", "TalentService",
    "MediaService",
]
