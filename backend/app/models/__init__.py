"""
数据库模型导出
"""
from .user import User
from .role import Role, user_roles
from .permission import Permission, role_permissions, department_permissions
from .department import Department, user_departments
from .police_type import PoliceType, user_police_types
from .system import Config, ConfigGroup, ConfigFormat
from .course import (
    Course, Chapter, CourseNote, CourseProgress, CourseTag, CourseTagRelation, CourseQA
)
from .training import (
    Training, TrainingBase, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem, TrainingHistory,
    TrainingCourseChangeLog,
)
from .exam import (
    KnowledgePoint, Question, ExamPaper, ExamPaperQuestion,
    AdmissionExam, AdmissionExamRecord,
    Exam, ExamQuestion, ExamRecord,
    question_knowledge_point_relations,
)
from .ai_task import AITask
from .personal_training_plan_snapshot import PersonalTrainingPlanSnapshot
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
    "Course", "Chapter", "CourseNote", "CourseProgress", "CourseTag", "CourseTagRelation", "CourseQA",
    # 培训相关
    "Training", "TrainingBase", "TrainingCourse", "Enrollment", "CheckinRecord", "ScheduleItem", "TrainingHistory",
    "TrainingCourseChangeLog",
    # 考试相关
    "KnowledgePoint", "Question", "ExamPaper", "ExamPaperQuestion",
    "AdmissionExam", "AdmissionExamRecord",
    "Exam", "ExamQuestion", "ExamRecord",
    "question_knowledge_point_relations",
    "AITask",
    "PersonalTrainingPlanSnapshot",
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
