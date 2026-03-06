"""
考试管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Question(Base):
    """题库表"""
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, comment='题目类型: single/multi/judge')
    content = Column(Text, nullable=False, comment='题干')
    options = Column(JSON, nullable=True, comment='选项 [{key, text}]')
    answer = Column(JSON, nullable=False, comment='答案 string或string[]')
    explanation = Column(Text, nullable=True, comment='解析')
    difficulty = Column(Integer, default=1, comment='难度1-5')
    knowledge_point = Column(String(200), nullable=True, comment='知识点')
    score = Column(Integer, default=1, comment='分值')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])


class Exam(Base):
    """考试表"""
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment='考试标题')
    description = Column(Text, nullable=True, comment='考试描述')
    duration = Column(Integer, default=60, comment='考试时长(分钟)')
    total_score = Column(Integer, default=100, comment='总分')
    passing_score = Column(Integer, default=60, comment='及格分')
    status = Column(String(50), default='upcoming', comment='状态: active/upcoming/ended')
    type = Column(String(50), default='formal', comment='类型: formal/quiz')
    scope = Column(String(200), nullable=True, comment='适用范围')
    start_time = Column(DateTime(timezone=True), nullable=True, comment='开始时间')
    end_time = Column(DateTime(timezone=True), nullable=True, comment='结束时间')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    """考试-题目关联表"""
    __tablename__ = 'exam_questions'

    exam_id = Column(Integer, ForeignKey('exams.id', ondelete='CASCADE'), primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)
    sort_order = Column(Integer, default=0, comment='题目排序')

    # 关联关系
    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question")


class ExamRecord(Base):
    """考试记录表"""
    __tablename__ = 'exam_records'

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False, comment='考试ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    score = Column(Integer, default=0, comment='得分')
    result = Column(String(20), nullable=True, comment='结果: pass/fail')
    grade = Column(String(5), nullable=True, comment='等级: A/B/C/D')
    start_time = Column(DateTime(timezone=True), nullable=True, comment='开始时间')
    end_time = Column(DateTime(timezone=True), nullable=True, comment='结束时间')
    duration = Column(Integer, default=0, comment='实际用时(分钟)')
    answers = Column(JSON, nullable=True, comment='答案 {questionId: answer}')
    correct_count = Column(Integer, default=0, comment='正确数')
    wrong_count = Column(Integer, default=0, comment='错误数')
    wrong_questions = Column(JSON, nullable=True, comment='错题列表 [questionId]')
    dimension_scores = Column(JSON, nullable=True, comment='维度得分 {law,enforce,evidence,physical,ethic}')

    # 关联关系
    exam = relationship("Exam", foreign_keys=[exam_id])
    user = relationship("User", foreign_keys=[user_id])
