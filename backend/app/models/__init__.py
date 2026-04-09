"""
数据库模型导出
"""
from .user import User
from .role import Role, user_roles
from .permission import Permission, role_permissions, department_permissions
from .department import Department, user_departments
from .police_type import PoliceType, user_police_types
from .training_type import TrainingType
from .dict_instructor_specialty import DictInstructorSpecialty
from .instructor_tag import InstructorTag
from .evaluation import EvaluationTemplate, EvaluationDimension, EvaluationTask, EvaluationTaskItem, EvaluationRecord, EvaluationScore
from .system import Config, ConfigGroup, ConfigFormat, DashboardModuleConfig
from .course import (
    Course, Chapter, CourseNote, CourseProgress, CourseTag, CourseTagRelation, CourseQA
)
from .training import (
    Training, TrainingBase, TrainingCourse, Enrollment, CheckinRecord, TrainingLeave, ScheduleItem, TrainingHistory,
    InstructorTeachingRecord, TrainingCourseChangeLog,
)
from .exam import (
    KnowledgePoint, Question, QuestionFolder, ExamPaper, PaperFolder, ExamPaperQuestion,
    AdmissionExam, AdmissionExamRecord,
    Exam, ExamQuestion, ExamRecord, ExamParticipant, ExamParticipantImportBatch,
    question_knowledge_point_relations,
    question_folder_course_relations,
)
from .ai_task import AITask
from .teaching_resource_generation_snapshot import TeachingResourceGenerationSnapshot
from .personal_training_plan_snapshot import PersonalTrainingPlanSnapshot
from .training_report_snapshot import TrainingReportSnapshot
from .certificate import Certificate
from .media import MediaFile
from .notice import Notice, NoticeRead
from .resource import (
    Resource, ResourceMediaLink, ResourceTag, ResourceTagRelation,
    ResourceVisibilityScope, CourseResourceRef, TrainingResourceRef,
    ResourceLike, ResourceComment,
)
from .library import LibraryFolder, LibraryItem
from .review import (
    ReviewPolicy, ReviewPolicyStage,
    ReviewWorkflow, ReviewTask, ReviewLog,
    ResourceReviewWorkflow, ResourceReviewTask, ResourceReviewLog,
)
from .recommendation import ResourceBehaviorEvent, ResourceRecommendScore
from .training_activity import TrainingActivity
from .training_plan import TrainingPlan
from .practice import PracticeRecord
from .video_keyframe import VideoKeyframeTask, VideoKeyframe
from .knowledge_base import KnowledgeBase, KnowledgeDocument
from .knowledge_chat_session import KnowledgeChatSession
from .scenario_template import ScenarioTemplate
from .scenario_session import ScenarioSession


__all__ = [
    "User",
    "Role",
    "Permission",
    "Department",
    "PoliceType",
    "Config",
    "ConfigGroup",
    "ConfigFormat",
    "DashboardModuleConfig",
    "user_roles",
    "role_permissions",
    "user_departments",
    "user_police_types",
    "TrainingType",
    "DictInstructorSpecialty",
    "InstructorTag",
    "EvaluationTemplate", "EvaluationDimension", "EvaluationTask", "EvaluationTaskItem", "EvaluationRecord", "EvaluationScore",
    "department_permissions",
    # 课程相关
    "Course", "Chapter", "CourseNote", "CourseProgress", "CourseTag", "CourseTagRelation", "CourseQA",
    # 培训相关
    "Training", "TrainingBase", "TrainingCourse", "Enrollment", "CheckinRecord", "TrainingLeave", "ScheduleItem", "TrainingHistory",
    "InstructorTeachingRecord", "TrainingCourseChangeLog",
    # 考试相关
    "KnowledgePoint", "Question", "QuestionFolder", "ExamPaper", "PaperFolder", "ExamPaperQuestion",
    "AdmissionExam", "AdmissionExamRecord",
    "Exam", "ExamQuestion", "ExamRecord", "ExamParticipant", "ExamParticipantImportBatch",
    "question_knowledge_point_relations",
    "question_folder_course_relations",
    "AITask",
    "TeachingResourceGenerationSnapshot",
    "PersonalTrainingPlanSnapshot",
    "TrainingReportSnapshot",
    # 证书
    "Certificate",
    # 文件
    "MediaFile",
    # 公告
    "Notice",
    "NoticeRead",
    # 资源库
    "Resource", "ResourceMediaLink", "ResourceTag", "ResourceTagRelation",
    "ResourceVisibilityScope", "CourseResourceRef", "TrainingResourceRef",
    "ResourceLike", "ResourceComment",
    "LibraryFolder", "LibraryItem",
    # 审核
    "ReviewPolicy", "ReviewPolicyStage",
    "ReviewWorkflow", "ReviewTask", "ReviewLog",
    "ResourceReviewWorkflow", "ResourceReviewTask", "ResourceReviewLog",
    # 推荐
    "ResourceBehaviorEvent", "ResourceRecommendScore",
    # 培训动态
    "TrainingActivity",
    # 培训计划
    "TrainingPlan",
    # 练习记录
    "PracticeRecord",
    # 视频关键帧
    "VideoKeyframeTask", "VideoKeyframe",
    # 知识库
    "KnowledgeBase", "KnowledgeDocument",
    "KnowledgeChatSession",
    # 场景模拟
    "ScenarioTemplate", "ScenarioSession",
]
