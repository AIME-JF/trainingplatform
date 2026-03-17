"""
考试管理服务
"""
from datetime import datetime
from math import ceil
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    AdmissionExam,
    AdmissionExamRecord,
    Department,
    Enrollment,
    Exam,
    ExamPaper,
    ExamPaperQuestion,
    ExamRecord,
    Question,
    Role,
    Training,
    User,
)
from app.schemas import PaginatedResponse
from app.schemas.exam import (
    ADMISSION_SCOPE_ALL,
    ADMISSION_SCOPE_DEPARTMENT,
    ADMISSION_SCOPE_ROLE,
    ADMISSION_SCOPE_USER,
    AdmissionExamCreate,
    AdmissionExamDetailResponse,
    AdmissionExamRecordResponse,
    AdmissionExamResponse,
    AdmissionExamUpdate,
    ExamCreate,
    ExamDetailResponse,
    ExamPaperCreate,
    ExamPaperDetailResponse,
    ExamPaperResponse,
    ExamPaperUpdate,
    ExamQuestionSnapshotResponse,
    ExamRecordResponse,
    ExamResponse,
    ExamSubmit,
    ExamUpdate,
    ExamWrongQuestionResponse,
)
from app.utils.authz import (
    can_view_question_with_context,
    can_view_training_with_context,
    is_admin_user,
    is_instructor_user,
)
from app.utils.data_scope import DataScopeContext, build_data_scope_context
from logger import logger


DIMENSION_KEYS = ("law", "enforce", "evidence", "physical", "ethic")
DIMENSION_RULES = {
    "law": ("法律", "法规", "条例", "法"),
    "enforce": ("执法", "程序", "处置", "侦查"),
    "evidence": ("证据", "取证", "笔录"),
    "physical": ("体能", "技能", "警械"),
    "ethic": ("道德", "纪律", "作风", "廉政"),
}
DEFAULT_EXAM_DURATION = 60
DEFAULT_PASSING_SCORE_RATIO = 0.6


class ExamService:
    """考试服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_exam_papers(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        paper_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[ExamPaperResponse]:
        """获取试卷列表"""
        query = self.db.query(ExamPaper).options(*self._paper_load_options())

        if status:
            query = query.filter(ExamPaper.status == status)
        if paper_type:
            query = query.filter(ExamPaper.type == paper_type)
        if search:
            query = query.filter(ExamPaper.title.contains(search))

        papers = query.order_by(ExamPaper.created_at.desc(), ExamPaper.id.desc()).all()
        scope_context = self._get_scope_context(current_user_id)
        if scope_context:
            papers = [paper for paper in papers if self._can_view_paper_with_context(scope_context, paper)]
        return self._paginate([self._to_paper_response(paper) for paper in papers], page, size)

    def get_exam_paper_detail(
        self,
        paper_id: int,
        current_user_id: Optional[int] = None,
    ) -> Optional[ExamPaperDetailResponse]:
        """获取试卷详情"""
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            return None
        scope_context = self._get_scope_context(current_user_id)
        if scope_context and not self._can_view_paper_with_context(scope_context, paper):
            return None
        return self._to_paper_detail_response(paper)

    def create_exam_paper(self, data: ExamPaperCreate, user_id: int) -> ExamPaperDetailResponse:
        """创建试卷"""
        questions = self._load_questions(data.question_ids or [])
        resolved_total_score = data.total_score or self._sum_question_scores(questions)
        paper = ExamPaper(
            title=data.title,
            description=data.description,
            duration=data.duration or 60,
            total_score=resolved_total_score,
            passing_score=data.passing_score or 60,
            type=data.type,
            status="draft",
            created_by=user_id,
        )
        self.db.add(paper)
        self.db.flush()
        self._replace_paper_questions(paper.id, data.question_ids, questions)
        self.db.commit()

        logger.info("创建试卷: %s", paper.title)
        detail = self.get_exam_paper_detail(paper.id, user_id)
        if not detail:
            raise ValueError("创建试卷后读取详情失败")
        return detail

    def update_exam_paper(self, paper_id: int, data: ExamPaperUpdate) -> ExamPaperDetailResponse:
        """更新试卷"""
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            raise ValueError("试卷不存在")
        if paper.status != "draft":
            raise ValueError("已发布或归档的试卷不能修改")

        update_data = data.model_dump(exclude_unset=True)
        question_ids = update_data.pop("question_ids", None)
        for field, value in update_data.items():
            setattr(paper, field, value)

        if question_ids is not None:
            questions = self._load_questions(question_ids)
            paper.total_score = data.total_score or self._sum_question_scores(questions)
            self._replace_paper_questions(paper.id, question_ids, questions)
        elif data.total_score is not None:
            paper.total_score = data.total_score

        self.db.commit()

        detail = self.get_exam_paper_detail(paper.id, paper.created_by)
        if not detail:
            raise ValueError("试卷不存在")
        return detail

    def publish_exam_paper(self, paper_id: int) -> ExamPaperDetailResponse:
        """发布试卷"""
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            raise ValueError("试卷不存在")
        if not (paper.paper_questions or []):
            raise ValueError("试卷至少需要配置一道题目")
        if paper.status == "published":
            detail = self.get_exam_paper_detail(paper.id, paper.created_by)
            if not detail:
                raise ValueError("试卷不存在")
            return detail

        paper.status = "published"
        paper.published_at = paper.published_at or self._current_time(paper.published_at)
        self.db.commit()

        detail = self.get_exam_paper_detail(paper.id, paper.created_by)
        if not detail:
            raise ValueError("试卷不存在")
        return detail

    def archive_exam_paper(self, paper_id: int) -> ExamPaperDetailResponse:
        """归档试卷"""
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            raise ValueError("试卷不存在")
        if paper.status == "archived":
            detail = self.get_exam_paper_detail(paper.id, paper.created_by)
            if not detail:
                raise ValueError("试卷不存在")
            return detail

        paper.status = "archived"
        self.db.commit()

        detail = self.get_exam_paper_detail(paper.id, paper.created_by)
        if not detail:
            raise ValueError("试卷不存在")
        return detail

    def delete_exam_paper(self, paper_id: int) -> None:
        """删除试卷"""
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            raise ValueError("试卷不存在")
        if self._paper_usage_count(paper) > 0:
            raise ValueError("试卷已被考试引用，不能删除")

        self.db.delete(paper)
        self.db.commit()

    def get_exams(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        training_id: Optional[int] = None,
        purpose: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[ExamResponse]:
        """获取培训班内考试列表"""
        query = self.db.query(Exam).options(
            joinedload(Exam.paper).joinedload(ExamPaper.paper_questions),
            joinedload(Exam.training),
            joinedload(Exam.records),
        ).filter(Exam.training_id.isnot(None))

        if exam_type:
            query = query.filter(Exam.type == exam_type)
        if search:
            query = query.filter(Exam.title.contains(search))
        if training_id:
            query = query.filter(Exam.training_id == training_id)
        if purpose:
            query = query.filter(Exam.purpose == purpose)

        exams = query.order_by(Exam.created_at.desc(), Exam.id.desc()).all()
        scope_context = self._get_scope_context(current_user_id)
        changed = False
        items: List[ExamResponse] = []
        for exam in exams:
            if self._refresh_exam_status(exam):
                changed = True
            if status and (exam.status or "upcoming") != status:
                continue
            if scope_context and not self._can_view_training_exam_with_context(scope_context, exam):
                continue
            items.append(self._to_training_exam_response(exam, current_user_id))

        if changed:
            self.db.commit()

        return self._paginate(items, page, size)

    def get_admission_exams(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[AdmissionExamResponse]:
        """获取独立准入考试列表"""
        current_user = self._get_admission_scope_user(current_user_id)
        can_manage_all = bool(current_user_id and self._can_manage_admission_exam(current_user_id))
        query = self.db.query(AdmissionExam).options(
            joinedload(AdmissionExam.paper).joinedload(ExamPaper.paper_questions),
            joinedload(AdmissionExam.linked_trainings),
            joinedload(AdmissionExam.records),
        )

        if exam_type:
            query = query.filter(AdmissionExam.type == exam_type)
        if search:
            query = query.filter(AdmissionExam.title.contains(search))

        exams = query.order_by(AdmissionExam.created_at.desc(), AdmissionExam.id.desc()).all()
        changed = False
        items: List[AdmissionExamResponse] = []
        for exam in exams:
            if self._refresh_exam_status(exam):
                changed = True
            if status and (exam.status or "upcoming") != status:
                continue
            if current_user_id and not can_manage_all:
                if not current_user or not self._can_view_admission_exam(exam, current_user):
                    continue
            items.append(self._to_admission_exam_response(exam, current_user_id, current_user))

        if changed:
            self.db.commit()

        return self._paginate(items, page, size)

    def create_exam(self, data: ExamCreate, user_id: int) -> ExamResponse:
        """创建培训班内考试"""
        training = self.db.query(Training).filter(Training.id == data.training_id).first()
        if not training:
            raise ValueError("关联培训班不存在")

        paper = self._get_selectable_paper(data.paper_id, user_id)
        duration = self._resolve_exam_duration(data.duration, paper.duration)
        passing_score = self._resolve_create_exam_passing_score(paper, data.passing_score)
        start_time, end_time = self._validate_exam_configuration(
            total_score=paper.total_score,
            duration=duration,
            passing_score=passing_score,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        exam = Exam(
            paper_id=paper.id,
            title=data.title,
            description=data.description,
            duration=duration,
            total_score=paper.total_score or 0,
            passing_score=passing_score,
            status=data.status,
            type=data.type or paper.type or "formal",
            purpose=data.purpose,
            training_id=data.training_id,
            max_attempts=data.max_attempts,
            allow_makeup=data.allow_makeup,
            start_time=start_time,
            end_time=end_time,
            published_at=self._current_time(start_time, end_time),
            created_by=user_id,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)

        logger.info("创建培训班内考试: %s", exam.title)
        detail = self.get_exam_detail(exam.id, user_id)
        if not detail:
            raise ValueError("创建考试后读取详情失败")
        return detail

    def create_admission_exam(self, data: AdmissionExamCreate, user_id: int) -> AdmissionExamResponse:
        """创建独立准入考试"""
        paper = self._get_selectable_paper(data.paper_id, user_id)
        scope_type, scope_target_ids, scope_summary = self._prepare_admission_scope(
            data.scope_type,
            data.scope_target_ids,
        )
        duration = self._resolve_exam_duration(data.duration, paper.duration)
        passing_score = self._resolve_create_exam_passing_score(paper, data.passing_score)
        start_time, end_time = self._validate_exam_configuration(
            total_score=paper.total_score,
            duration=duration,
            passing_score=passing_score,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        exam = AdmissionExam(
            paper_id=paper.id,
            title=data.title,
            description=data.description,
            duration=duration,
            total_score=paper.total_score or 0,
            passing_score=passing_score,
            status=data.status,
            type=data.type or paper.type or "formal",
            scope=scope_summary,
            scope_type=scope_type,
            scope_target_ids=scope_target_ids,
            max_attempts=data.max_attempts,
            start_time=start_time,
            end_time=end_time,
            published_at=self._current_time(start_time, end_time),
            created_by=user_id,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)

        logger.info("创建准入考试: %s", exam.title)
        detail = self.get_admission_exam_detail(exam.id, user_id)
        if not detail:
            raise ValueError("创建准入考试后读取详情失败")
        return detail

    def update_exam(self, exam_id: int, data: ExamUpdate) -> ExamResponse:
        """更新培训班内考试"""
        exam = self.db.query(Exam).options(
            joinedload(Exam.paper).joinedload(ExamPaper.paper_questions),
        ).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")

        if data.training_id is not None:
            training = self.db.query(Training).filter(Training.id == data.training_id).first()
            if not training:
                raise ValueError("关联培训班不存在")

        self._update_training_exam(exam, data)
        self.db.commit()
        self.db.refresh(exam)

        detail = self.get_exam_detail(exam.id)
        if not detail:
            raise ValueError("考试不存在")
        return detail

    def update_admission_exam(self, exam_id: int, data: AdmissionExamUpdate) -> AdmissionExamResponse:
        """更新独立准入考试"""
        exam = self.db.query(AdmissionExam).options(
            joinedload(AdmissionExam.paper).joinedload(ExamPaper.paper_questions),
        ).filter(AdmissionExam.id == exam_id).first()
        if not exam:
            raise ValueError("准入考试不存在")

        self._update_admission_exam_entity(exam, data)
        self.db.commit()
        self.db.refresh(exam)

        detail = self.get_admission_exam_detail(exam.id)
        if not detail:
            raise ValueError("准入考试不存在")
        return detail

    def get_exam_detail(
        self,
        exam_id: int,
        current_user_id: Optional[int] = None,
    ) -> Optional[ExamDetailResponse]:
        """获取培训班内考试详情"""
        exam = self.db.query(Exam).options(
            joinedload(Exam.paper).joinedload(ExamPaper.paper_questions),
            joinedload(Exam.training),
            joinedload(Exam.records),
        ).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        if self._refresh_exam_status(exam):
            self.db.commit()
        scope_context = self._get_scope_context(current_user_id)
        if scope_context and not self._can_view_training_exam_with_context(scope_context, exam):
            return None

        return ExamDetailResponse(
            **self._to_training_exam_response(exam, current_user_id).model_dump(),
            questions=self._build_snapshot_responses(exam.paper),
        )

    def get_admission_exam_detail(
        self,
        exam_id: int,
        current_user_id: Optional[int] = None,
    ) -> Optional[AdmissionExamDetailResponse]:
        """获取准入考试详情"""
        exam = self.db.query(AdmissionExam).options(
            joinedload(AdmissionExam.paper).joinedload(ExamPaper.paper_questions),
            joinedload(AdmissionExam.linked_trainings),
            joinedload(AdmissionExam.records),
        ).filter(AdmissionExam.id == exam_id).first()
        if not exam:
            return None

        if self._refresh_exam_status(exam):
            self.db.commit()

        current_user = self._get_admission_scope_user(current_user_id)
        can_manage_all = bool(current_user_id and self._can_manage_admission_exam(current_user_id))
        if current_user_id and not can_manage_all:
            if not current_user or not self._can_view_admission_exam(exam, current_user):
                return None

        return AdmissionExamDetailResponse(
            **self._to_admission_exam_response(exam, current_user_id, current_user).model_dump(),
            questions=self._build_snapshot_responses(exam.paper),
        )

    def submit_exam(self, exam_id: int, user_id: int, data: ExamSubmit) -> ExamRecordResponse:
        """提交培训班内考试"""
        exam = self.db.query(Exam).options(
            joinedload(Exam.paper).joinedload(ExamPaper.paper_questions),
            joinedload(Exam.training),
        ).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")

        if self._refresh_exam_status(exam):
            self.db.commit()
        if exam.status != "active":
            raise ValueError("当前考试未开放作答")

        attempt_count = self._count_submitted_attempts(ExamRecord, ExamRecord.exam_id, exam.id, user_id)
        if not self._can_join_training_exam(exam, user_id, attempt_count):
            raise ValueError("当前用户无权参加该考试")

        record = self._build_exam_record(
            exam=exam,
            user_id=user_id,
            data=data,
            record_class=ExamRecord,
            exam_field_name="exam_id",
            attempt_count=attempt_count,
        )
        self.db.add(record)
        self._update_user_exam_stats(user_id, record.score or 0)
        self.db.commit()

        saved = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.user),
            joinedload(ExamRecord.exam),
        ).filter(ExamRecord.id == record.id).first()
        logger.info("用户%s提交培训班考试%s，得分=%s", user_id, exam_id, saved.score if saved else 0)
        return self._to_training_record_response(saved or record, exam)

    def submit_admission_exam(self, exam_id: int, user_id: int, data: ExamSubmit) -> AdmissionExamRecordResponse:
        """提交准入考试"""
        exam = self.db.query(AdmissionExam).options(
            joinedload(AdmissionExam.paper).joinedload(ExamPaper.paper_questions),
        ).filter(AdmissionExam.id == exam_id).first()
        if not exam:
            raise ValueError("准入考试不存在")

        if self._refresh_exam_status(exam):
            self.db.commit()
        if exam.status != "active":
            raise ValueError("当前准入考试未开放作答")

        attempt_count = self._count_submitted_attempts(
            AdmissionExamRecord,
            AdmissionExamRecord.admission_exam_id,
            exam.id,
            user_id,
        )
        current_user = self._get_admission_scope_user(user_id)
        if not self._can_join_admission_exam(exam, user_id, attempt_count, current_user):
            raise ValueError("当前用户不在准入考试适用范围内或已达到最大作答次数")

        record = self._build_exam_record(
            exam=exam,
            user_id=user_id,
            data=data,
            record_class=AdmissionExamRecord,
            exam_field_name="admission_exam_id",
            attempt_count=attempt_count,
        )
        self.db.add(record)
        self._update_user_exam_stats(user_id, record.score or 0)
        self.db.commit()

        saved = self.db.query(AdmissionExamRecord).options(
            joinedload(AdmissionExamRecord.user),
            joinedload(AdmissionExamRecord.admission_exam),
        ).filter(AdmissionExamRecord.id == record.id).first()
        logger.info("用户%s提交准入考试%s，得分=%s", user_id, exam_id, saved.score if saved else 0)
        return self._to_admission_record_response(saved or record, exam)

    def get_exam_result(self, exam_id: int, user_id: int) -> Optional[ExamRecordResponse]:
        """获取培训班内考试结果"""
        record = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.user),
            joinedload(ExamRecord.exam),
        ).filter(
            ExamRecord.exam_id == exam_id,
            ExamRecord.user_id == user_id,
        ).order_by(ExamRecord.end_time.desc(), ExamRecord.id.desc()).first()
        if not record:
            return None
        return self._to_training_record_response(record, record.exam)

    def get_admission_exam_result(self, exam_id: int, user_id: int) -> Optional[AdmissionExamRecordResponse]:
        """获取准入考试结果"""
        record = self.db.query(AdmissionExamRecord).options(
            joinedload(AdmissionExamRecord.user),
            joinedload(AdmissionExamRecord.admission_exam),
        ).filter(
            AdmissionExamRecord.admission_exam_id == exam_id,
            AdmissionExamRecord.user_id == user_id,
        ).order_by(AdmissionExamRecord.end_time.desc(), AdmissionExamRecord.id.desc()).first()
        if not record:
            return None
        return self._to_admission_record_response(record, record.admission_exam)

    def get_exam_scores(self, exam_id: int, page: int = 1, size: int = 10) -> PaginatedResponse[ExamRecordResponse]:
        """获取培训班内考试成绩列表"""
        query = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.user),
            joinedload(ExamRecord.exam),
        ).filter(
            ExamRecord.exam_id == exam_id,
        ).order_by(ExamRecord.score.desc(), ExamRecord.id.asc())
        total = query.count()
        rows = query.all() if size == -1 else query.offset((page - 1) * size).limit(size).all()
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_training_record_response(row, row.exam) for row in rows],
        )

    def get_admission_exam_scores(
        self,
        exam_id: int,
        page: int = 1,
        size: int = 10,
    ) -> PaginatedResponse[AdmissionExamRecordResponse]:
        """获取准入考试成绩列表"""
        query = self.db.query(AdmissionExamRecord).options(
            joinedload(AdmissionExamRecord.user),
            joinedload(AdmissionExamRecord.admission_exam),
        ).filter(
            AdmissionExamRecord.admission_exam_id == exam_id,
        ).order_by(AdmissionExamRecord.score.desc(), AdmissionExamRecord.id.asc())
        total = query.count()
        rows = query.all() if size == -1 else query.offset((page - 1) * size).limit(size).all()
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_admission_record_response(row, row.admission_exam) for row in rows],
        )

    def get_exam_analysis(self, exam_id: int) -> Dict[str, Any]:
        """获取培训班内考试分析"""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError("考试不存在")
        return self._build_analysis(
            self.db.query(ExamRecord).options(
                joinedload(ExamRecord.user).joinedload(User.departments),
            ).filter(
                ExamRecord.exam_id == exam_id,
                ExamRecord.status == "submitted",
            ).order_by(ExamRecord.score.desc()).all(),
            exam.passing_score or 60,
        )

    def get_admission_exam_analysis(self, exam_id: int) -> Dict[str, Any]:
        """获取准入考试分析"""
        exam = self.db.query(AdmissionExam).filter(AdmissionExam.id == exam_id).first()
        if not exam:
            raise ValueError("准入考试不存在")
        return self._build_analysis(
            self.db.query(AdmissionExamRecord).options(
                joinedload(AdmissionExamRecord.user).joinedload(User.departments),
            ).filter(
                AdmissionExamRecord.admission_exam_id == exam_id,
                AdmissionExamRecord.status == "submitted",
            ).order_by(AdmissionExamRecord.score.desc()).all(),
            exam.passing_score or 60,
        )

    def _build_analysis(self, records: List[Any], passing_score: int) -> Dict[str, Any]:
        students = []
        for record in records:
            user = record.user
            department_name = "未知单位"
            if user and user.departments:
                department_name = user.departments[0].name
            dimensions = record.dimension_scores or {}
            students.append({
                "id": record.id,
                "name": user.nickname if user and user.nickname else (user.username if user else "未知"),
                "policeId": user.police_id if user else "",
                "unit": department_name,
                "score": record.score or 0,
                "law": dimensions.get("law", 0),
                "enforce": dimensions.get("enforce", 0),
                "evidence": dimensions.get("evidence", 0),
                "physical": dimensions.get("physical", 0),
                "ethic": dimensions.get("ethic", 0),
                "time": f"{record.duration or 0}分钟",
                "pass": (record.score or 0) >= passing_score,
            })
        return {
            "students": students,
            "passing_score": passing_score,
        }

    def _paper_load_options(self) -> tuple:
        return (
            selectinload(ExamPaper.paper_questions).joinedload(ExamPaperQuestion.question),
            selectinload(ExamPaper.training_exams),
            selectinload(ExamPaper.admission_exams),
        )

    def _get_scope_context(self, current_user_id: Optional[int]) -> Optional[DataScopeContext]:
        if not current_user_id:
            return None
        return build_data_scope_context(self.db, current_user_id)

    def _can_view_paper_with_context(
        self,
        scope_context: Optional[DataScopeContext],
        paper: Optional[ExamPaper],
    ) -> bool:
        if not paper:
            return False
        if scope_context is None:
            return True

        paper_questions = sorted(paper.paper_questions or [], key=lambda item: item.sort_order or 0)
        if not paper_questions:
            return True

        for paper_question in paper_questions:
            question = paper_question.question
            if question is None:
                if paper.created_by and paper.created_by == scope_context.user_id:
                    continue
                return False
            if not can_view_question_with_context(scope_context, question):
                return False
        return True

    def _can_view_training_exam_with_context(
        self,
        scope_context: Optional[DataScopeContext],
        exam: Optional[Exam],
    ) -> bool:
        if not exam:
            return False
        if scope_context is None:
            return True
        if not exam.training:
            return False
        return can_view_training_with_context(scope_context, exam.training)

    def _get_paper_detail_entity(self, paper_id: int) -> Optional[ExamPaper]:
        return self.db.query(ExamPaper).options(*self._paper_load_options()).filter(ExamPaper.id == paper_id).first()

    def _get_selectable_paper(self, paper_id: int, current_user_id: Optional[int] = None) -> ExamPaper:
        paper = self._get_paper_detail_entity(paper_id)
        if not paper:
            raise ValueError("试卷不存在")
        scope_context = self._get_scope_context(current_user_id)
        if scope_context and not self._can_view_paper_with_context(scope_context, paper):
            raise ValueError("无权使用该试卷")
        if paper.status != "published":
            raise ValueError("只能选择已发布试卷")
        if not (paper.paper_questions or []):
            raise ValueError("试卷未配置题目")
        return paper

    def _sum_question_scores(self, questions: List[Question]) -> int:
        return sum(int(question.score or 0) for question in questions)

    def _paper_usage_count(self, paper: ExamPaper) -> int:
        return len(paper.training_exams or []) + len(paper.admission_exams or [])

    def _load_questions(self, question_ids: List[int]) -> List[Question]:
        if not question_ids:
            raise ValueError("请至少选择一道题目")
        questions = self.db.query(Question).filter(Question.id.in_(question_ids)).all()
        question_map = {question.id: question for question in questions}
        ordered_questions = [question_map.get(question_id) for question_id in question_ids]
        if not all(ordered_questions):
            raise ValueError("存在无效题目，无法创建试卷")
        return ordered_questions

    def _update_training_exam(self, exam: Exam, data: ExamUpdate) -> None:
        update_data = data.model_dump(exclude_unset=True)
        paper_id = update_data.pop("paper_id", None)
        if paper_id is not None and paper_id != exam.paper_id:
            raise ValueError("考试已发布，不能更换试卷")

        next_start_time = update_data.get("start_time", exam.start_time)
        next_end_time = update_data.get("end_time", exam.end_time)
        next_duration = self._resolve_exam_duration(update_data.get("duration"), exam.duration)
        next_passing_score = self._resolve_existing_exam_passing_score(
            exam.paper,
            update_data.get("passing_score"),
            exam.passing_score,
        )
        start_time, end_time = self._validate_exam_configuration(
            total_score=exam.paper.total_score,
            duration=next_duration,
            passing_score=next_passing_score,
            start_time=next_start_time,
            end_time=next_end_time,
        )

        for field, value in update_data.items():
            setattr(exam, field, value)

        exam.duration = next_duration
        exam.passing_score = next_passing_score
        exam.start_time = start_time
        exam.end_time = end_time
        exam.total_score = exam.paper.total_score or exam.total_score or 0
        if exam.status in {"active", "ended"} and not exam.published_at:
            exam.published_at = self._current_time(exam.start_time, exam.end_time, exam.published_at)

    def _update_admission_exam_entity(self, exam: AdmissionExam, data: AdmissionExamUpdate) -> None:
        update_data = data.model_dump(exclude_unset=True)
        paper_id = update_data.pop("paper_id", None)
        if paper_id is not None and paper_id != exam.paper_id:
            raise ValueError("准入考试已发布，不能更换试卷")

        next_scope_type = update_data.pop("scope_type", exam.scope_type or ADMISSION_SCOPE_ALL)
        next_scope_target_ids = update_data.pop("scope_target_ids", exam.scope_target_ids or [])
        update_data.pop("scope", None)
        next_start_time = update_data.get("start_time", exam.start_time)
        next_end_time = update_data.get("end_time", exam.end_time)
        next_duration = self._resolve_exam_duration(update_data.get("duration"), exam.duration)
        next_passing_score = self._resolve_existing_exam_passing_score(
            exam.paper,
            update_data.get("passing_score"),
            exam.passing_score,
        )
        start_time, end_time = self._validate_exam_configuration(
            total_score=exam.paper.total_score,
            duration=next_duration,
            passing_score=next_passing_score,
            start_time=next_start_time,
            end_time=next_end_time,
        )

        for field, value in update_data.items():
            setattr(exam, field, value)

        scope_type, scope_target_ids, scope_summary = self._prepare_admission_scope(
            next_scope_type,
            next_scope_target_ids,
        )
        exam.scope_type = scope_type
        exam.scope_target_ids = scope_target_ids
        exam.scope = scope_summary
        exam.duration = next_duration
        exam.passing_score = next_passing_score
        exam.start_time = start_time
        exam.end_time = end_time
        exam.total_score = exam.paper.total_score or exam.total_score or 0
        if exam.status in {"active", "ended"} and not exam.published_at:
            exam.published_at = self._current_time(exam.start_time, exam.end_time, exam.published_at)

    def _resolve_exam_duration(self, preferred: Optional[int], fallback: Optional[int]) -> int:
        value = preferred if preferred is not None else fallback
        return int(value or DEFAULT_EXAM_DURATION)

    def _resolve_create_exam_passing_score(self, paper: ExamPaper, preferred: Optional[int]) -> int:
        total_score = int(paper.total_score or 0)
        if total_score <= 0:
            raise ValueError("试卷满分必须大于0")
        if preferred is not None:
            return int(preferred)

        fallback = int(paper.passing_score or 0)
        if 0 < fallback <= total_score:
            return fallback
        return max(1, int(ceil(total_score * DEFAULT_PASSING_SCORE_RATIO)))

    def _resolve_existing_exam_passing_score(
        self,
        paper: ExamPaper,
        preferred: Optional[int],
        fallback: Optional[int],
    ) -> int:
        if preferred is not None:
            return int(preferred)
        if fallback is not None:
            return int(fallback)
        return self._resolve_create_exam_passing_score(paper, None)

    def _validate_exam_configuration(
        self,
        *,
        total_score: Optional[int],
        duration: int,
        passing_score: int,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        resolved_total_score = int(total_score or 0)
        if resolved_total_score <= 0:
            raise ValueError("试卷满分必须大于0")
        if duration < 10:
            raise ValueError("考试时长不能少于10分钟")
        if passing_score < 1:
            raise ValueError("及格分不能小于1分")
        if passing_score > resolved_total_score:
            raise ValueError(f"及格分不能超过试卷满分（{resolved_total_score}分）")

        now = self._current_time(start_time, end_time)
        normalized_start = self._normalize_datetime(start_time, now.tzinfo)
        normalized_end = self._normalize_datetime(end_time, now.tzinfo)
        if normalized_start and normalized_end:
            if normalized_end <= normalized_start:
                raise ValueError("考试结束时间必须晚于开始时间")

        return normalized_start, normalized_end

    def _can_manage_admission_exam(self, user_id: int) -> bool:
        return is_admin_user(self.db, user_id) or is_instructor_user(self.db, user_id)

    def _get_admission_scope_user(self, user_id: Optional[int]) -> Optional[User]:
        if not user_id:
            return None
        return self.db.query(User).options(
            joinedload(User.roles),
            joinedload(User.departments),
        ).filter(
            User.id == user_id,
            User.is_active == True,
        ).first()

    def _normalize_scope_target_ids(self, values: Any) -> List[int]:
        normalized: List[int] = []
        seen = set()
        for raw_item in values or []:
            try:
                item = int(raw_item)
            except (TypeError, ValueError):
                continue
            if item <= 0 or item in seen:
                continue
            seen.add(item)
            normalized.append(item)
        return normalized

    def _prepare_admission_scope(
        self,
        scope_type: Optional[str],
        scope_target_ids: Any,
    ) -> tuple[str, List[int], str]:
        resolved_scope_type = str(scope_type or ADMISSION_SCOPE_ALL).strip() or ADMISSION_SCOPE_ALL
        target_ids = self._normalize_scope_target_ids(scope_target_ids)

        if resolved_scope_type == ADMISSION_SCOPE_ALL:
            return ADMISSION_SCOPE_ALL, [], "全体学员"

        if not target_ids:
            raise ValueError("请至少选择一个适用范围目标")

        if resolved_scope_type == ADMISSION_SCOPE_USER:
            users = self.db.query(User).options(joinedload(User.roles)).filter(
                User.id.in_(target_ids),
                User.is_active == True,
            ).all()
            user_map = {
                user.id: user
                for user in users
                if self._is_student_user(user)
            }
            ordered_users = [user_map.get(item_id) for item_id in target_ids]
            if not all(ordered_users):
                raise ValueError("指定用户中包含无效学员")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定用户", [self._display_user_name(user) for user in ordered_users]),
            )

        if resolved_scope_type == ADMISSION_SCOPE_DEPARTMENT:
            departments = self.db.query(Department).filter(
                Department.id.in_(target_ids),
                Department.is_active == True,
            ).all()
            department_map = {department.id: department for department in departments}
            ordered_departments = [department_map.get(item_id) for item_id in target_ids]
            if not all(ordered_departments):
                raise ValueError("指定部门中包含无效部门")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定部门", [department.name for department in ordered_departments]),
            )

        if resolved_scope_type == ADMISSION_SCOPE_ROLE:
            roles = self.db.query(Role).filter(
                Role.id.in_(target_ids),
                Role.is_active == True,
            ).all()
            role_map = {role.id: role for role in roles}
            ordered_roles = [role_map.get(item_id) for item_id in target_ids]
            if not all(ordered_roles):
                raise ValueError("指定角色中包含无效角色")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定角色", [role.name for role in ordered_roles]),
            )

        raise ValueError("不支持的适用范围类型")

    def _build_scope_summary(self, label: str, names: List[str]) -> str:
        cleaned_names = [str(name).strip() for name in names if str(name or "").strip()]
        if not cleaned_names:
            return label
        if len(cleaned_names) <= 3:
            return f"{label}：{'、'.join(cleaned_names)}"
        return f"{label}：{'、'.join(cleaned_names[:3])} 等{len(cleaned_names)}项"

    def _display_user_name(self, user: Optional[User]) -> str:
        if not user:
            return ""
        return str(user.nickname or user.username or user.id)

    def _is_student_user(self, user: Optional[User]) -> bool:
        if not user:
            return False
        return any(str(role.code or "").strip() == "student" for role in (user.roles or []))

    def _can_view_admission_exam(self, exam: AdmissionExam, user: Optional[User]) -> bool:
        if not user or not user.is_active or not self._is_student_user(user):
            return False

        scope_type = exam.scope_type or ADMISSION_SCOPE_ALL
        target_ids = set(self._normalize_scope_target_ids(exam.scope_target_ids))
        if scope_type == ADMISSION_SCOPE_ALL:
            return True
        if not target_ids:
            return False
        if scope_type == ADMISSION_SCOPE_USER:
            return user.id in target_ids
        if scope_type == ADMISSION_SCOPE_DEPARTMENT:
            return any(department.id in target_ids for department in (user.departments or []))
        if scope_type == ADMISSION_SCOPE_ROLE:
            return any(role.id in target_ids for role in (user.roles or []))
        return False

    def _replace_paper_questions(self, paper_id: int, question_ids: List[int], questions: List[Question]) -> None:
        question_map = {question.id: question for question in questions}
        self.db.query(ExamPaperQuestion).filter(
            ExamPaperQuestion.paper_id == paper_id,
        ).delete(synchronize_session=False)
        for index, question_id in enumerate(question_ids):
            question = question_map[question_id]
            self.db.add(ExamPaperQuestion(
                paper_id=paper_id,
                question_id=question_id,
                sort_order=index,
                question_type=question.type,
                content=question.content,
                options=question.options,
                answer=question.answer,
                explanation=question.explanation,
                score=question.score or 0,
                knowledge_point=question.knowledge_point,
            ))

    def _build_snapshot_responses(self, paper: Optional[ExamPaper]) -> List[ExamQuestionSnapshotResponse]:
        if not paper:
            return []
        return [
            ExamQuestionSnapshotResponse(
                id=item.question_id,
                type=item.question_type or (item.question.type if item.question else "single"),
                content=item.content or (item.question.content if item.question else ""),
                options=item.options if item.options is not None else (item.question.options if item.question else None),
                answer=item.answer if item.answer is not None else (item.question.answer if item.question else None),
                explanation=item.explanation if item.explanation is not None else (item.question.explanation if item.question else None),
                score=int(item.score or (item.question.score if item.question else 0) or 0),
                knowledge_point=item.knowledge_point or (item.question.knowledge_point if item.question else None),
            )
            for item in sorted(paper.paper_questions or [], key=lambda row: row.sort_order or 0)
        ]

    def _to_paper_response(self, paper: ExamPaper) -> ExamPaperResponse:
        linked_exam_count = len(paper.training_exams or [])
        linked_admission_exam_count = len(paper.admission_exams or [])
        return ExamPaperResponse(
            id=paper.id,
            title=paper.title,
            description=paper.description,
            duration=paper.duration or 60,
            total_score=paper.total_score or 0,
            passing_score=paper.passing_score or 60,
            type=paper.type or "formal",
            status=paper.status or "draft",
            published_at=paper.published_at,
            created_by=paper.created_by,
            question_count=len(paper.paper_questions or []),
            usage_count=linked_exam_count + linked_admission_exam_count,
            linked_exam_count=linked_exam_count,
            linked_admission_exam_count=linked_admission_exam_count,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
        )

    def _to_paper_detail_response(self, paper: ExamPaper) -> ExamPaperDetailResponse:
        return ExamPaperDetailResponse(
            **self._to_paper_response(paper).model_dump(),
            questions=self._build_snapshot_responses(paper),
        )

    def _build_exam_record(
        self,
        exam: Any,
        user_id: int,
        data: ExamSubmit,
        record_class: Any,
        exam_field_name: str,
        attempt_count: int,
    ) -> Any:
        snapshots = self._build_snapshot_responses(exam.paper)
        if not snapshots:
            raise ValueError("考试未配置题目")

        score = 0
        correct_count = 0
        wrong_count = 0
        wrong_questions: List[int] = []
        wrong_details: List[ExamWrongQuestionResponse] = []
        dimension_totals = {key: 0 for key in DIMENSION_KEYS}
        dimension_gains = {key: 0 for key in DIMENSION_KEYS}

        for snapshot in snapshots:
            question_score = int(snapshot.score or 0)
            dimension = self._resolve_dimension(snapshot.knowledge_point)
            dimension_totals[dimension] += question_score

            user_answer = data.answers.get(str(snapshot.id))
            correct_answer = self._resolve_correct_answer(exam.paper, snapshot.id)
            if self._is_correct_answer(snapshot.type, user_answer, correct_answer):
                score += question_score
                correct_count += 1
                dimension_gains[dimension] += question_score
                continue

            wrong_count += 1
            wrong_questions.append(snapshot.id)
            wrong_details.append(ExamWrongQuestionResponse(
                question_id=snapshot.id,
                type=snapshot.type,
                content=snapshot.content,
                my_answer=user_answer,
                answer=correct_answer,
                explanation=snapshot.explanation,
                score=question_score,
            ))

        now = self._current_time(data.start_time)
        start_time = self._normalize_datetime(data.start_time, now.tzinfo)
        duration = 0
        if start_time:
            duration = max(0, int((now - start_time).total_seconds() / 60))
        dimension_scores = {
            key: int(round((dimension_gains[key] / dimension_totals[key]) * 100))
            if dimension_totals[key] > 0 else 0
            for key in DIMENSION_KEYS
        }
        payload = {
            exam_field_name: exam.id,
            "paper_id": exam.paper_id,
            "user_id": user_id,
            "attempt_no": attempt_count + 1,
            "status": "submitted",
            "score": score,
            "result": "pass" if score >= int(exam.passing_score or 60) else "fail",
            "grade": self._resolve_grade(score),
            "start_time": start_time,
            "end_time": now,
            "duration": duration,
            "answers": data.answers,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "wrong_questions": wrong_questions,
            "wrong_question_details": [row.model_dump() for row in wrong_details],
            "dimension_scores": dimension_scores,
        }
        return record_class(**payload)

    def _resolve_correct_answer(self, paper: Optional[ExamPaper], question_id: int) -> Any:
        if not paper:
            return None
        for row in paper.paper_questions or []:
            if row.question_id != question_id:
                continue
            if row.answer is not None:
                return row.answer
            if row.question:
                return row.question.answer
        return None

    def _count_submitted_attempts(self, model: Any, field: Any, exam_id: int, user_id: int) -> int:
        return self.db.query(model).filter(
            field == exam_id,
            model.user_id == user_id,
            model.status == "submitted",
        ).count()

    def _to_training_exam_response(self, exam: Exam, current_user_id: Optional[int] = None) -> ExamResponse:
        attempt_count = 0
        latest_result = None
        can_join = None
        if current_user_id:
            latest_record = self.db.query(ExamRecord).filter(
                ExamRecord.exam_id == exam.id,
                ExamRecord.user_id == current_user_id,
            ).order_by(ExamRecord.end_time.desc(), ExamRecord.id.desc()).first()
            if latest_record:
                attempt_count = self._count_submitted_attempts(ExamRecord, ExamRecord.exam_id, exam.id, current_user_id)
                latest_result = latest_record.result
            can_join = self._can_join_training_exam(exam, current_user_id, attempt_count)

        return ExamResponse(
            id=exam.id,
            paper_id=exam.paper_id,
            paper_title=exam.paper.title if exam.paper else None,
            paper_status=exam.paper.status if exam.paper else None,
            title=exam.title,
            description=exam.description,
            duration=exam.duration or 60,
            total_score=exam.total_score or 0,
            passing_score=exam.passing_score or 60,
            status=exam.status or "upcoming",
            type=exam.type or "formal",
            purpose=exam.purpose or "class_assessment",
            training_id=exam.training_id,
            training_name=exam.training.name if exam.training else None,
            max_attempts=exam.max_attempts or 1,
            allow_makeup=bool(exam.allow_makeup),
            start_time=exam.start_time,
            end_time=exam.end_time,
            created_by=exam.created_by,
            question_count=len(exam.paper.paper_questions or []) if exam.paper else 0,
            attempt_count=attempt_count,
            latest_result=latest_result,
            can_join=can_join,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
        )

    def _to_admission_exam_response(
        self,
        exam: AdmissionExam,
        current_user_id: Optional[int] = None,
        current_user: Optional[User] = None,
    ) -> AdmissionExamResponse:
        attempt_count = 0
        latest_result = None
        can_join = None
        if current_user_id:
            latest_record = self.db.query(AdmissionExamRecord).filter(
                AdmissionExamRecord.admission_exam_id == exam.id,
                AdmissionExamRecord.user_id == current_user_id,
            ).order_by(AdmissionExamRecord.end_time.desc(), AdmissionExamRecord.id.desc()).first()
            if latest_record:
                attempt_count = self._count_submitted_attempts(
                    AdmissionExamRecord,
                    AdmissionExamRecord.admission_exam_id,
                    exam.id,
                    current_user_id,
                )
                latest_result = latest_record.result
            can_join = self._can_join_admission_exam(exam, current_user_id, attempt_count, current_user)

        return AdmissionExamResponse(
            id=exam.id,
            paper_id=exam.paper_id,
            paper_title=exam.paper.title if exam.paper else None,
            paper_status=exam.paper.status if exam.paper else None,
            title=exam.title,
            description=exam.description,
            duration=exam.duration or 60,
            total_score=exam.total_score or 0,
            passing_score=exam.passing_score or 60,
            status=exam.status or "upcoming",
            type=exam.type or "formal",
            scope=exam.scope or "全体学员",
            scope_type=exam.scope_type or ADMISSION_SCOPE_ALL,
            scope_target_ids=self._normalize_scope_target_ids(exam.scope_target_ids),
            max_attempts=exam.max_attempts or 1,
            linked_training_count=len(exam.linked_trainings or []),
            attempt_count=attempt_count,
            latest_result=latest_result,
            can_join=can_join,
            created_by=exam.created_by,
            question_count=len(exam.paper.paper_questions or []) if exam.paper else 0,
            start_time=exam.start_time,
            end_time=exam.end_time,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
        )

    def _to_training_record_response(self, record: ExamRecord, exam: Optional[Exam]) -> ExamRecordResponse:
        details = [
            ExamWrongQuestionResponse.model_validate(item)
            for item in (record.wrong_question_details or [])
        ]
        user = record.user if getattr(record, "user", None) else None
        return ExamRecordResponse(
            id=record.id,
            exam_id=record.exam_id,
            paper_id=record.paper_id,
            exam_title=exam.title if exam else None,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            attempt_no=record.attempt_no or 1,
            status=record.status or "submitted",
            score=record.score or 0,
            result=record.result,
            grade=record.grade,
            passing_score=exam.passing_score if exam else None,
            start_time=record.start_time,
            end_time=record.end_time,
            duration=record.duration or 0,
            correct_count=record.correct_count or 0,
            wrong_count=record.wrong_count or 0,
            wrong_questions=record.wrong_questions or [],
            wrong_question_details=details,
            dimension_scores=record.dimension_scores or {},
        )

    def _to_admission_record_response(
        self,
        record: AdmissionExamRecord,
        exam: Optional[AdmissionExam],
    ) -> AdmissionExamRecordResponse:
        details = [
            ExamWrongQuestionResponse.model_validate(item)
            for item in (record.wrong_question_details or [])
        ]
        user = record.user if getattr(record, "user", None) else None
        return AdmissionExamRecordResponse(
            id=record.id,
            exam_id=record.admission_exam_id,
            paper_id=record.paper_id,
            exam_title=exam.title if exam else None,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            attempt_no=record.attempt_no or 1,
            status=record.status or "submitted",
            score=record.score or 0,
            result=record.result,
            grade=record.grade,
            passing_score=exam.passing_score if exam else None,
            start_time=record.start_time,
            end_time=record.end_time,
            duration=record.duration or 0,
            correct_count=record.correct_count or 0,
            wrong_count=record.wrong_count or 0,
            wrong_questions=record.wrong_questions or [],
            wrong_question_details=details,
            dimension_scores=record.dimension_scores or {},
        )

    @staticmethod
    def _is_aware_datetime(value: Optional[datetime]) -> bool:
        return bool(value and value.tzinfo and value.tzinfo.utcoffset(value) is not None)

    @classmethod
    def _current_time(cls, *references: Optional[datetime]) -> datetime:
        for reference in references:
            if cls._is_aware_datetime(reference):
                return datetime.now(reference.tzinfo)
        return datetime.now()

    @classmethod
    def _normalize_datetime(cls, value: Optional[datetime], reference_tzinfo: Any) -> Optional[datetime]:
        if value is None:
            return None
        if cls._is_aware_datetime(value) or reference_tzinfo is None:
            return value
        return value.replace(tzinfo=reference_tzinfo)

    def _refresh_exam_status(self, exam: Any) -> bool:
        now = self._current_time(exam.start_time, exam.end_time)
        start_time = self._normalize_datetime(exam.start_time, now.tzinfo)
        end_time = self._normalize_datetime(exam.end_time, now.tzinfo)
        next_status = exam.status or "upcoming"
        if start_time and end_time:
            if now < start_time:
                next_status = "upcoming"
            elif start_time <= now <= end_time:
                next_status = "active"
            else:
                next_status = "ended"
        elif end_time and now > end_time:
            next_status = "ended"
        elif start_time and now >= start_time:
            next_status = "active"
        if next_status != exam.status:
            exam.status = next_status
            return True
        return False

    def _can_join_training_exam(self, exam: Exam, user_id: int, attempt_count: int) -> bool:
        if exam.status != "active":
            return False
        if attempt_count >= int(exam.max_attempts or 1):
            return False
        enrollment = self.db.query(Enrollment.id).filter(
            Enrollment.training_id == exam.training_id,
            Enrollment.user_id == user_id,
            Enrollment.status == "approved",
        ).first()
        return enrollment is not None

    def _can_join_admission_exam(
        self,
        exam: AdmissionExam,
        user_id: int,
        attempt_count: int,
        current_user: Optional[User] = None,
    ) -> bool:
        if exam.status != "active":
            return False
        if attempt_count >= int(exam.max_attempts or 1):
            return False
        user = current_user or self._get_admission_scope_user(user_id)
        return self._can_view_admission_exam(exam, user)

    def _is_correct_answer(self, question_type: str, user_answer: Any, correct_answer: Any) -> bool:
        if question_type == "multi":
            if not isinstance(user_answer, list) or not isinstance(correct_answer, list):
                return False
            return sorted(str(item) for item in user_answer) == sorted(str(item) for item in correct_answer)
        return self._normalize_scalar_answer(user_answer) == self._normalize_scalar_answer(correct_answer)

    def _normalize_scalar_answer(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().upper()
        if text in {"TRUE", "T", "A", "YES", "Y"}:
            return "T"
        if text in {"FALSE", "F", "B", "NO", "N"}:
            return "F"
        return text

    def _resolve_dimension(self, knowledge_point: Optional[str]) -> str:
        if not knowledge_point:
            return "law"
        for dimension, keywords in DIMENSION_RULES.items():
            if any(keyword in knowledge_point for keyword in keywords):
                return dimension
        return "law"

    def _resolve_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 60:
            return "C"
        return "D"

    def _update_user_exam_stats(self, user_id: int, score: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        previous_count = user.exam_count or 0
        previous_total = float(user.avg_score or 0) * previous_count
        user.exam_count = previous_count + 1
        user.avg_score = (previous_total + score) / user.exam_count

    def _paginate(self, items: List[Any], page: int, size: int) -> PaginatedResponse[Any]:
        total = len(items)
        page_items = items
        if size != -1:
            start = (page - 1) * size
            page_items = items[start:start + size]
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=page_items,
        )
