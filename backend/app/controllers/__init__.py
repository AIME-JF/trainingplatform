"""
控制器导出
"""
from .user import UserController
from .role import RoleController
from .permission import PermissionController
from .department import DepartmentController
from .police_type import PoliceTypeController
from .system import SystemConfigController
from .course import CourseController
from .exam import ExamController
from .question import QuestionController
from .training import TrainingController
from .instructor import InstructorController
from .certificate import CertificateController
from .profile import ProfileController
from .dashboard import DashboardController
from .report import ReportController
from .ai import AIController
from .talent import TalentController

__all__ = [
    "UserController",
    "RoleController",
    "PermissionController",
    "DepartmentController",
    "PoliceTypeController",
    "SystemConfigController",
    "CourseController",
    "ExamController",
    "QuestionController",
    "TrainingController",
    "InstructorController",
    "CertificateController",
    "ProfileController",
    "DashboardController",
    "ReportController",
    "AIController",
    "TalentController",
]
