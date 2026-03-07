"""
数据库模型导出
"""
from .user import User
from .role import Role, user_roles
from .permission import Permission, role_permissions, department_permissions
from .department import Department, user_departments
from .police_type import PoliceType, user_police_types
from .system import Config, ConfigGroup, ConfigFormat
from .course import Course, Chapter, CourseNote, CourseProgress
from .training import Training, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem
from .exam import Question, Exam, ExamQuestion, ExamRecord
from .certificate import Certificate
from .instructor import InstructorProfile
from .media import MediaFile


__all__ = [
    "User",
    "Role",
    "Permission",
    "Department",
    "PoliceType",
    "Config",
    "ConfigGroup",
    "ConfigFormat",
    "user_roles",
    "role_permissions",
    "user_departments",
    "user_police_types",
    "department_permissions",
    # 课程相关
    "Course", "Chapter", "CourseNote", "CourseProgress",
    # 培训相关
    "Training", "TrainingCourse", "Enrollment", "CheckinRecord", "ScheduleItem",
    # 考试相关
    "Question", "Exam", "ExamQuestion", "ExamRecord",
    # 证书
    "Certificate",
    # 教官
    "InstructorProfile",
    # 文件
    "MediaFile",
]
