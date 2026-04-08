"""
教官授课档案服务
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import (
    CheckinRecord,
    Enrollment,
    InstructorTeachingRecord,
    Training,
    TrainingCourse,
    User,
)
from app.schemas.training import (
    InstructorTeachingRecordResponse,
    InstructorTeachingSummaryResponse,
)
from logger import logger


class InstructorService:
    def __init__(self, db: Session):
        self.db = db

    def refresh_teaching_records(self, training_id: int) -> None:
        """刷新培训班关联教官的授课档案（培训班结束或课次完成时调用）"""
        training = self.db.query(Training).options(
            joinedload(Training.courses).joinedload(TrainingCourse.primary_instructor),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return

        approved_count = sum(1 for e in (training.enrollments or []) if e.status == "approved")

        for course in (training.courses or []):
            instructor_ids = []
            roles = {}
            if course.primary_instructor_id:
                instructor_ids.append(course.primary_instructor_id)
                roles[course.primary_instructor_id] = "primary"
            for aid in (course.assistant_instructor_ids or []):
                aid_int = int(aid)
                if aid_int not in roles:
                    instructor_ids.append(aid_int)
                    roles[aid_int] = "assistant"

            # 计算该课程的教学评价均分
            eval_avg = self._calc_course_evaluation_avg(training_id, course)

            for uid in instructor_ids:
                record = self.db.query(InstructorTeachingRecord).filter(
                    InstructorTeachingRecord.user_id == uid,
                    InstructorTeachingRecord.training_id == training_id,
                    InstructorTeachingRecord.training_course_id == course.id,
                ).first()

                if not record:
                    record = InstructorTeachingRecord(
                        user_id=uid,
                        training_id=training_id,
                        training_course_id=course.id,
                    )
                    self.db.add(record)

                record.training_name = training.name
                record.course_name = course.name
                record.location = course.location or training.location
                record.hours = course.hours or 0
                record.role = roles.get(uid, "primary")
                record.student_count = approved_count
                record.evaluation_avg = eval_avg
                record.start_date = training.start_date
                record.end_date = training.end_date
                record.archived_at = datetime.now()

        self.db.commit()
        logger.info("刷新教官授课档案: training_id=%s", training_id)

    def get_teaching_summary(self, user_id: int, year: Optional[int] = None) -> InstructorTeachingSummaryResponse:
        """获取教官训历聚合统计"""
        query = self.db.query(InstructorTeachingRecord).options(
            joinedload(InstructorTeachingRecord.training),
        ).filter(
            InstructorTeachingRecord.user_id == user_id,
        )
        if year:
            query = query.filter(
                InstructorTeachingRecord.start_date != None,
                self.db.func.extract("year", InstructorTeachingRecord.start_date) == year,
            )
        records = query.order_by(InstructorTeachingRecord.start_date.desc()).all()

        training_ids = set()
        total_hours = 0.0
        course_names = []
        eval_scores = []
        student_total = 0

        for r in records:
            training_ids.add(r.training_id)
            total_hours += r.hours or 0
            if r.course_name and r.course_name not in course_names:
                course_names.append(r.course_name)
            if r.evaluation_avg is not None:
                eval_scores.append(r.evaluation_avg)
            student_total += r.student_count or 0

        return InstructorTeachingSummaryResponse(
            user_id=user_id,
            training_count=len(training_ids),
            total_hours=round(total_hours, 1),
            course_names=course_names,
            evaluation_avg=round(sum(eval_scores) / len(eval_scores), 2) if eval_scores else None,
            student_total=student_total,
            records=[self._to_response(r) for r in records],
        )

    def get_teaching_records(self, user_id: int, year: Optional[int] = None) -> List[InstructorTeachingRecordResponse]:
        """获取教官授课记录列表"""
        query = self.db.query(InstructorTeachingRecord).options(
            joinedload(InstructorTeachingRecord.training),
        ).filter(
            InstructorTeachingRecord.user_id == user_id,
        )
        if year:
            query = query.filter(
                InstructorTeachingRecord.start_date != None,
                self.db.func.extract("year", InstructorTeachingRecord.start_date) == year,
            )
        records = query.order_by(InstructorTeachingRecord.start_date.desc()).all()
        return [self._to_response(r) for r in records]

    def _calc_course_evaluation_avg(self, training_id: int, course: TrainingCourse) -> Optional[float]:
        """计算某课程所有课次的学员评课均分"""
        session_keys = []
        for schedule in (course.schedules or []):
            sid = schedule.get("session_id") if isinstance(schedule, dict) else None
            if sid:
                session_keys.append(sid)
        if not session_keys:
            return None

        scores = self.db.query(CheckinRecord.evaluation_score).filter(
            CheckinRecord.training_id == training_id,
            CheckinRecord.session_key.in_(session_keys),
            CheckinRecord.evaluation_score != None,
        ).all()
        if not scores:
            return None
        return round(sum(s[0] for s in scores) / len(scores), 2)

    def _to_response(self, record: InstructorTeachingRecord) -> InstructorTeachingRecordResponse:
        training_status = None
        if record.training:
            training_status = record.training.status or "upcoming"
        return InstructorTeachingRecordResponse(
            id=record.id,
            user_id=record.user_id,
            training_id=record.training_id,
            training_course_id=record.training_course_id,
            training_name=record.training_name,
            training_status=training_status,
            course_name=record.course_name,
            location=record.location,
            hours=record.hours or 0,
            role=record.role or "primary",
            student_count=record.student_count or 0,
            evaluation_avg=record.evaluation_avg,
            start_date=record.start_date,
            end_date=record.end_date,
            archived_at=record.archived_at,
        )
