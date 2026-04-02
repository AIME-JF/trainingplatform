"""
考试管理相关的数据库模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


question_knowledge_point_relations = Table(
    "question_knowledge_point_relations",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("knowledge_point_id", Integer, ForeignKey("knowledge_points.id", ondelete="CASCADE"), primary_key=True),
)


class KnowledgePoint(Base):
    """知识点表"""

    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="知识点名称")
    description = Column(Text, nullable=True, comment="知识点描述")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, comment="课程ID")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    course = relationship("Course", back_populates="knowledge_points")
    questions = relationship(
        "Question",
        secondary=question_knowledge_point_relations,
        back_populates="knowledge_points",
    )


class Question(Base):
    """题库表"""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, comment="题目类型: single/multi/judge")
    content = Column(Text, nullable=False, comment="题干")
    options = Column(JSON, nullable=True, comment="选项 [{key, text}]")
    answer = Column(JSON, nullable=False, comment="答案 string 或 string[]")
    explanation = Column(Text, nullable=True, comment="解析")
    difficulty = Column(Integer, default=1, comment="难度1-5")
    police_type_id = Column(Integer, ForeignKey("police_types.id"), nullable=True, comment="警种ID")
    score = Column(Integer, default=1, comment="分值")
    folder_id = Column(Integer, ForeignKey("question_folders.id"), nullable=True, comment="所属文件夹ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    police_type = relationship("PoliceType", foreign_keys=[police_type_id])
    folder = relationship("QuestionFolder", back_populates="questions")
    knowledge_points = relationship(
        "KnowledgePoint",
        secondary=question_knowledge_point_relations,
        back_populates="questions",
    )


class QuestionFolder(Base):
    """试题文件夹表"""

    __tablename__ = "question_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="文件夹名称")
    category = Column(String(50), nullable=True, comment="题库分类")
    parent_id = Column(Integer, ForeignKey("question_folders.id"), nullable=True, comment="父文件夹ID")
    sort_order = Column(Integer, default=0, comment="排序")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    parent = relationship("QuestionFolder", remote_side=[id], backref="children")
    questions = relationship("Question", back_populates="folder")


class PaperFolder(Base):
    """试卷文件夹表"""

    __tablename__ = "paper_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="文件夹名称")
    parent_id = Column(Integer, ForeignKey("paper_folders.id"), nullable=True, comment="父文件夹ID")
    sort_order = Column(Integer, default=0, comment="排序")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    parent = relationship("PaperFolder", remote_side=[id], backref="children")
    papers = relationship("ExamPaper", back_populates="folder")


class ExamPaper(Base):
    """试卷表"""

    __tablename__ = "exam_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="试卷标题")
    description = Column(Text, nullable=True, comment="试卷描述")
    duration = Column(Integer, default=60, comment="考试时长(分钟)")
    total_score = Column(Integer, default=100, comment="总分")
    passing_score = Column(Integer, default=60, comment="及格分")
    type = Column(String(50), default="formal", comment="试卷类型: formal/quiz")
    status = Column(String(20), default="draft", comment="试卷状态: draft/published/archived")
    folder_id = Column(Integer, ForeignKey("paper_folders.id"), nullable=True, comment="所属文件夹ID")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    folder = relationship("PaperFolder", back_populates="papers")
    paper_questions = relationship(
        "ExamPaperQuestion",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    training_exams = relationship("Exam", back_populates="paper")
    admission_exams = relationship("AdmissionExam", back_populates="paper")


class ExamPaperQuestion(Base):
    """试卷与题目关联表，同时固化题目快照"""

    __tablename__ = "exam_paper_questions"

    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    sort_order = Column(Integer, default=0, comment="题目排序")
    question_type = Column(String(20), nullable=True, comment="题目类型快照")
    content = Column(Text, nullable=True, comment="题干快照")
    options = Column(JSON, nullable=True, comment="选项快照")
    answer = Column(JSON, nullable=True, comment="答案快照")
    explanation = Column(Text, nullable=True, comment="解析快照")
    score = Column(Integer, default=1, comment="分值快照")
    knowledge_points = Column(JSON, nullable=True, comment="知识点快照")

    paper = relationship("ExamPaper", back_populates="paper_questions")
    question = relationship("Question")


class AdmissionExam(Base):
    """独立准入考试表，不直接隶属培训班"""

    __tablename__ = "admission_exams"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id"), nullable=False, comment="试卷ID")
    title = Column(String(200), nullable=False, comment="准入考试标题")
    description = Column(Text, nullable=True, comment="准入考试描述")
    duration = Column(Integer, default=60, comment="考试时长(分钟)")
    total_score = Column(Integer, default=100, comment="总分")
    passing_score = Column(Integer, default=60, comment="及格分")
    status = Column(String(50), default="upcoming", comment="状态: active/upcoming/ended")
    type = Column(String(50), default="formal", comment="展示类型: formal/quiz")
    scope = Column(String(200), nullable=True, comment="适用范围摘要")
    scope_type = Column(String(30), default="all", comment="适用范围类型: all/user/department/role")
    scope_target_ids = Column(JSON, nullable=True, comment="适用范围目标ID列表")
    course_ids = Column(JSON, nullable=True, comment="显式绑定课程ID列表")
    max_attempts = Column(Integer, default=1, comment="最大作答次数")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    paper = relationship("ExamPaper", back_populates="admission_exams")
    records = relationship(
        "AdmissionExamRecord",
        back_populates="admission_exam",
        cascade="all, delete-orphan",
    )
    linked_trainings = relationship("Training", back_populates="admission_exam")


class Exam(Base):
    """培训班内考试表"""

    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id"), nullable=False, comment="试卷ID")
    title = Column(String(200), nullable=False, comment="场次标题")
    description = Column(Text, nullable=True, comment="场次描述")
    duration = Column(Integer, default=60, comment="考试时长(分钟)")
    total_score = Column(Integer, default=100, comment="总分")
    passing_score = Column(Integer, default=60, comment="及格分")
    status = Column(String(50), default="upcoming", comment="状态: active/upcoming/ended")
    type = Column(String(50), default="formal", comment="展示类型: formal/quiz")
    purpose = Column(
        String(50),
        default="class_assessment",
        comment="用途: class_assessment/final_assessment/quiz/makeup",
    )
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False, comment="关联培训班ID")
    course_ids = Column(JSON, nullable=True, comment="显式绑定课程ID列表")
    max_attempts = Column(Integer, default=1, comment="最大作答次数")
    allow_makeup = Column(Boolean, default=False, comment="是否允许补考")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    paper = relationship("ExamPaper", back_populates="training_exams")
    training = relationship("Training", back_populates="exam_sessions", foreign_keys=[training_id])
    records = relationship(
        "ExamRecord",
        back_populates="exam",
        cascade="all, delete-orphan",
    )
    exam_questions = relationship(
        "ExamQuestion",
        foreign_keys="ExamQuestion.exam_id",
        back_populates="exam",
        cascade="all, delete-orphan",
    )


class ExamQuestion(Base):
    """
    培训考试题目快照表

    已有历史表保留，用于兼容旧数据；新逻辑统一从试卷快照读取。
    """

    __tablename__ = "exam_questions"

    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(Integer, primary_key=True, comment="来源题目ID")
    sort_order = Column(Integer, default=0, comment="题目排序")
    question_type = Column(String(20), nullable=False, comment="题目类型")
    content = Column(Text, nullable=False, comment="题干快照")
    options = Column(JSON, nullable=True, comment="选项快照")
    answer = Column(JSON, nullable=False, comment="答案快照")
    explanation = Column(Text, nullable=True, comment="解析快照")
    score = Column(Integer, default=1, comment="分值快照")
    knowledge_points = Column(JSON, nullable=True, comment="知识点快照")

    exam = relationship("Exam", foreign_keys=[exam_id], back_populates="exam_questions")


class AdmissionExamRecord(Base):
    """准入考试作答记录表"""

    __tablename__ = "admission_exam_records"

    id = Column(Integer, primary_key=True, index=True)
    admission_exam_id = Column(Integer, ForeignKey("admission_exams.id"), nullable=False, comment="准入考试ID")
    paper_id = Column(Integer, ForeignKey("exam_papers.id"), nullable=False, comment="试卷ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    attempt_no = Column(Integer, default=1, comment="第几次作答")
    status = Column(String(20), default="submitted", comment="状态: submitted/absent/exempt")
    score = Column(Integer, default=0, comment="得分")
    result = Column(String(20), nullable=True, comment="结果: pass/fail")
    grade = Column(String(5), nullable=True, comment="等级: A/B/C/D")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    duration = Column(Integer, default=0, comment="实际用时(分钟)")
    answers = Column(JSON, nullable=True, comment="答案 {questionId: answer}")
    correct_count = Column(Integer, default=0, comment="正确数")
    wrong_count = Column(Integer, default=0, comment="错误数")
    wrong_questions = Column(JSON, nullable=True, comment="错题列表 [questionId]")
    wrong_question_details = Column(JSON, nullable=True, comment="错题详情快照")
    dimension_scores = Column(
        JSON,
        nullable=True,
        comment="维度得分 {law,enforce,evidence,physical,ethic}",
    )
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), comment="提交时间")

    admission_exam = relationship("AdmissionExam", back_populates="records", foreign_keys=[admission_exam_id])
    paper = relationship("ExamPaper", foreign_keys=[paper_id])
    user = relationship("User", foreign_keys=[user_id])


class ExamRecord(Base):
    """培训班考试作答记录表"""

    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, comment="考试场次ID")
    paper_id = Column(Integer, ForeignKey("exam_papers.id"), nullable=False, comment="试卷ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    attempt_no = Column(Integer, default=1, comment="第几次作答")
    status = Column(String(20), default="submitted", comment="状态: submitted/absent/exempt")
    score = Column(Integer, default=0, comment="得分")
    result = Column(String(20), nullable=True, comment="结果: pass/fail")
    grade = Column(String(5), nullable=True, comment="等级: A/B/C/D")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    duration = Column(Integer, default=0, comment="实际用时(分钟)")
    answers = Column(JSON, nullable=True, comment="答案 {questionId: answer}")
    correct_count = Column(Integer, default=0, comment="正确数")
    wrong_count = Column(Integer, default=0, comment="错误数")
    wrong_questions = Column(JSON, nullable=True, comment="错题列表 [questionId]")
    wrong_question_details = Column(JSON, nullable=True, comment="错题详情快照")
    dimension_scores = Column(
        JSON,
        nullable=True,
        comment="维度得分 {law,enforce,evidence,physical,ethic}",
    )
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), comment="提交时间")

    exam = relationship("Exam", back_populates="records", foreign_keys=[exam_id])
    paper = relationship("ExamPaper", foreign_keys=[paper_id])
    user = relationship("User", foreign_keys=[user_id])
