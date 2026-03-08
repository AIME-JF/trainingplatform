"""
考试管理服务
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Exam, ExamQuestion, ExamRecord, Question, User
from app.schemas.exam import (
    ExamCreate, ExamUpdate, ExamResponse, ExamDetailResponse,
    ExamSubmit, ExamRecordResponse, QuestionResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class ExamService:
    """考试服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_exams(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[ExamResponse]:
        """获取考试列表"""
        query = self.db.query(Exam)

        if status:
            query = query.filter(Exam.status == status)
        if type:
            query = query.filter(Exam.type == type)
        if search:
            query = query.filter(Exam.title.contains(search))

        query = query.order_by(Exam.created_at.desc())
        total = query.count()

        if size == -1:
            exams = query.all()
        else:
            skip = (page - 1) * size
            exams = query.offset(skip).limit(size).all()

        items = []
        for e in exams:
            q_count = self.db.query(ExamQuestion).filter(ExamQuestion.exam_id == e.id).count()
            items.append(ExamResponse(
                id=e.id, title=e.title, description=e.description,
                duration=e.duration, total_score=e.total_score,
                passing_score=e.passing_score, status=e.status,
                type=e.type, scope=e.scope,
                start_time=e.start_time, end_time=e.end_time,
                created_by=e.created_by, question_count=q_count,
                created_at=e.created_at, updated_at=e.updated_at
            ))

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def create_exam(self, data: ExamCreate, user_id: int) -> ExamResponse:
        """创建考试"""
        exam = Exam(
            title=data.title, description=data.description,
            duration=data.duration, total_score=data.total_score,
            passing_score=data.passing_score, status=data.status,
            type=data.type, scope=data.scope,
            start_time=data.start_time, end_time=data.end_time,
            created_by=user_id
        )
        self.db.add(exam)
        self.db.flush()

        # 关联题目
        if data.question_ids:
            for idx, qid in enumerate(data.question_ids):
                eq = ExamQuestion(exam_id=exam.id, question_id=qid, sort_order=idx)
                self.db.add(eq)

        self.db.commit()
        self.db.refresh(exam)
        logger.info(f"创建考试: {exam.title}")

        q_count = len(data.question_ids) if data.question_ids else 0
        return ExamResponse(
            id=exam.id, title=exam.title, description=exam.description,
            duration=exam.duration, total_score=exam.total_score,
            passing_score=exam.passing_score, status=exam.status,
            type=exam.type, scope=exam.scope,
            start_time=exam.start_time, end_time=exam.end_time,
            created_by=exam.created_by, question_count=q_count,
            created_at=exam.created_at, updated_at=exam.updated_at
        )

    def get_exam_detail(self, exam_id: int) -> Optional[ExamDetailResponse]:
        """获取考试详情（含题目）"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        eq_list = self.db.query(ExamQuestion).options(
            joinedload(ExamQuestion.question)
        ).filter(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.sort_order).all()

        questions = [QuestionResponse.model_validate(eq.question) for eq in eq_list if eq.question]

        return ExamDetailResponse(
            id=exam.id, title=exam.title, description=exam.description,
            duration=exam.duration, total_score=exam.total_score,
            passing_score=exam.passing_score, status=exam.status,
            type=exam.type, scope=exam.scope,
            start_time=exam.start_time, end_time=exam.end_time,
            created_by=exam.created_by, question_count=len(questions),
            created_at=exam.created_at, updated_at=exam.updated_at,
            questions=questions
        )

    def submit_exam(self, exam_id: int, user_id: int, data: ExamSubmit) -> ExamRecordResponse:
        """提交考试"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")

        # 获取考试题目
        eq_list = self.db.query(ExamQuestion).options(
            joinedload(ExamQuestion.question)
        ).filter(ExamQuestion.exam_id == exam_id).all()

        # 批改
        correct_count = 0
        wrong_count = 0
        wrong_questions = []
        total_score = 0

        for eq in eq_list:
            q = eq.question
            if not q:
                continue
            q_id_str = str(q.id)
            user_answer = data.answers.get(q_id_str)
            correct_answer = q.answer

            is_correct = False
            if q.type == 'multi':
                if isinstance(user_answer, list) and isinstance(correct_answer, list):
                    is_correct = sorted(user_answer) == sorted(correct_answer)
            else:
                is_correct = str(user_answer) == str(correct_answer)

            if is_correct:
                correct_count += 1
                total_score += q.score
            else:
                wrong_count += 1
                wrong_questions.append(q.id)

        # 判定结果
        result = "pass" if total_score >= exam.passing_score else "fail"
        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "D"

        now = datetime.now()
        duration = 0
        if data.start_time:
            duration = int((now - data.start_time).total_seconds() / 60)

        record = ExamRecord(
            exam_id=exam_id, user_id=user_id,
            score=total_score, result=result, grade=grade,
            start_time=data.start_time, end_time=now,
            duration=duration, answers=data.answers,
            correct_count=correct_count, wrong_count=wrong_count,
            wrong_questions=wrong_questions
        )
        self.db.add(record)

        # 更新用户统计
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.exam_count = (user.exam_count or 0) + 1
            old_total = (user.avg_score or 0) * ((user.exam_count or 1) - 1)
            user.avg_score = (old_total + total_score) / user.exam_count

        self.db.commit()
        self.db.refresh(record)
        logger.info(f"用户{user_id}提交考试{exam_id}, 得分{total_score}")

        return ExamRecordResponse(
            id=record.id, exam_id=record.exam_id,
            exam_title=exam.title,
            user_id=record.user_id, score=record.score,
            result=record.result, grade=record.grade,
            start_time=record.start_time, end_time=record.end_time,
            duration=record.duration, correct_count=record.correct_count,
            wrong_count=record.wrong_count,
            wrong_questions=record.wrong_questions,
            dimension_scores=record.dimension_scores
        )

    def get_exam_result(self, exam_id: int, user_id: int) -> Optional[ExamRecordResponse]:
        """获取考试结果"""
        record = self.db.query(ExamRecord).filter(
            ExamRecord.exam_id == exam_id,
            ExamRecord.user_id == user_id
        ).order_by(ExamRecord.end_time.desc()).first()

        if not record:
            return None

        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        return ExamRecordResponse(
            id=record.id, exam_id=record.exam_id,
            exam_title=exam.title if exam else None,
            user_id=record.user_id, score=record.score,
            result=record.result, grade=record.grade,
            start_time=record.start_time, end_time=record.end_time,
            duration=record.duration, correct_count=record.correct_count,
            wrong_count=record.wrong_count,
            wrong_questions=record.wrong_questions,
            dimension_scores=record.dimension_scores
        )

    def get_exam_scores(
        self, exam_id: int, page: int = 1, size: int = 10
    ) -> PaginatedResponse[ExamRecordResponse]:
        """获取考试成绩列表（教官/管理员）"""
        query = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.user)
        ).filter(ExamRecord.exam_id == exam_id)

        total = query.count()
        query = query.order_by(ExamRecord.score.desc())

        if size == -1:
            records = query.all()
        else:
            skip = (page - 1) * size
            records = query.offset(skip).limit(size).all()

        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()

        items = []
        for r in records:
            items.append(ExamRecordResponse(
                id=r.id, exam_id=r.exam_id,
                exam_title=exam.title if exam else None,
                user_id=r.user_id,
                user_name=r.user.username if r.user else None,
                user_nickname=r.user.nickname if r.user else None,
                score=r.score, result=r.result, grade=r.grade,
                start_time=r.start_time, end_time=r.end_time,
                duration=r.duration, correct_count=r.correct_count,
                wrong_count=r.wrong_count,
                wrong_questions=r.wrong_questions,
                dimension_scores=r.dimension_scores
            ))

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def get_exam_analysis(self, exam_id: int) -> Dict[str, Any]:
        """获取考试成绩分析数据"""
        records = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.user).joinedload(User.departments)
        ).filter(ExamRecord.exam_id == exam_id).order_by(ExamRecord.score.desc()).all()

        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()

        students = []
        for r in records:
            u = r.user
            unit_name = "未知单位"
            if u and u.departments:
                unit_name = u.departments[0].name
            
            dims = r.dimension_scores or {}
            
            students.append({
                "id": r.id,
                "name": u.nickname if u and u.nickname else (u.username if u else "未知"),
                "policeId": u.police_id if u else "",
                "unit": unit_name,
                "score": r.score,
                "law": dims.get("law", 0),
                "enforce": dims.get("enforce", 0),
                "evidence": dims.get("evidence", 0),
                "physical": dims.get("physical", 0),
                "ethic": dims.get("ethic", 0),
                "time": f"{r.duration}分钟",
                "pass": r.score >= (exam.passing_score if exam else 60)
            })

        return {
            "students": students,
            "passing_score": exam.passing_score if exam else 60
        }

