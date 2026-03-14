"""
数据库模型导出
"""
from .user import User
from .role import Role, user_roles
from .permission import Permission, role_permissions, department_permissions
from .department import Department, user_departments
from .police_type import PoliceType, user_police_types
from .system import Config, ConfigGroup, ConfigFormat
from .course import Course, Chapter, CourseNote, CourseProgress, CourseQA
from .training import (
    Training, TrainingBase, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem, TrainingHistory
)
from .exam import (
    Question, ExamPaper, ExamPaperQuestion,
    AdmissionExam, AdmissionExamRecord,
    Exam, ExamQuestion, ExamRecord,
)
from .ai_task import AITask
from .certificate import Certificate
from .media import MediaFile
from .notice import Notice
from .resource import (
    Resource, ResourceMediaLink, ResourceTag, ResourceTagRelation,
    ResourceVisibilityScope, CourseResourceRef, TrainingResourceRef
)
from .review import (
    ReviewPolicy, ReviewPolicyStage, ResourceReviewWorkflow,
    ResourceReviewTask, ResourceReviewLog
)
from .recommendation import ResourceBehaviorEvent, ResourceRecommendScore


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
    "Course", "Chapter", "CourseNote", "CourseProgress", "CourseQA",
    # 培训相关
    "Training", "TrainingBase", "TrainingCourse", "Enrollment", "CheckinRecord", "ScheduleItem", "TrainingHistory",
    # 考试相关
    "Question", "ExamPaper", "ExamPaperQuestion",
    "AdmissionExam", "AdmissionExamRecord",
    "Exam", "ExamQuestion", "ExamRecord",
    "AITask",
    # 证书
    "Certificate",
    # 文件
    "MediaFile",
    # 公告
    "Notice",
    # 资源库
    "Resource", "ResourceMediaLink", "ResourceTag", "ResourceTagRelation",
    "ResourceVisibilityScope", "CourseResourceRef", "TrainingResourceRef",
    # 审核
    "ReviewPolicy", "ReviewPolicyStage", "ResourceReviewWorkflow",
    "ResourceReviewTask", "ResourceReviewLog",
    # 推荐
    "ResourceBehaviorEvent", "ResourceRecommendScore",
]
