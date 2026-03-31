"""
工作台服务
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.models import (
    User, Course, Exam, Training, ExamRecord, Enrollment, CourseProgress
)
from app.schemas.dashboard import DashboardResponse
from app.services.course_progress import CourseProgressService
from logger import logger


class DashboardService:
    """工作台服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: int, role: str) -> DashboardResponse:
        """根据角色返回不同数据"""
        if role == 'admin':
            return self._admin_dashboard()
        elif role == 'instructor':
            return self._instructor_dashboard(user_id)
        else:
            return self._student_dashboard(user_id)

    def _admin_dashboard(self) -> DashboardResponse:
        """管理员工作台"""
        total_users = self.db.query(User).filter(User.is_active == True).count()
        total_courses = self.db.query(Course).count()
        total_exams = self.db.query(Exam).count()
        active_trainings = self.db.query(Training).filter(Training.status == 'active').count()

        recent_courses = self.db.query(Course).order_by(
            Course.created_at.desc()
        ).limit(5).all()

        recent_exams = self.db.query(Exam).order_by(
            Exam.created_at.desc()
        ).limit(5).all()

        recent_trainings = self.db.query(Training).order_by(
            Training.created_at.desc()
        ).limit(5).all()

        return DashboardResponse(
            stats={
                "total_users": total_users,
                "total_courses": total_courses,
                "total_exams": total_exams,
                "active_trainings": active_trainings
            },
            recent_courses=[{"id": c.id, "title": c.title, "category": c.category} for c in recent_courses],
            recent_exams=[{"id": e.id, "title": e.title, "status": e.status} for e in recent_exams],
            recent_trainings=[{
                "name": t.name,
                "status": t.status or "upcoming",
                "start_date": t.start_date.strftime("%Y-%m-%d") if t.start_date else "",
                "enrolled": len(t.enrollments) if t.enrollments else 0
            } for t in recent_trainings]
        )

    def _instructor_dashboard(self, user_id: int) -> DashboardResponse:
        """教官工作台"""
        my_courses = self.db.query(Course).filter(Course.instructor_id == user_id).count()
        my_trainings = self.db.query(Training).filter(Training.instructor_id == user_id).count()
        my_exams = self.db.query(Exam).filter(Exam.created_by == user_id).count()

        pending_enrollments = self.db.query(Enrollment).join(Training).filter(
            Training.instructor_id == user_id,
            Enrollment.status == 'pending'
        ).count()

        return DashboardResponse(
            stats={
                "my_courses": my_courses,
                "my_trainings": my_trainings,
                "my_exams": my_exams,
                "pending_enrollments": pending_enrollments
            }
        )

    def _student_dashboard(self, user_id: int) -> DashboardResponse:
        """学员工作台"""
        course_ids = {
            course_id
            for (course_id,) in self.db.query(CourseProgress.course_id).filter(
                CourseProgress.user_id == user_id
            ).distinct().all()
            if course_id is not None
        }
        courses = []
        if course_ids:
            courses = (
                self.db.query(Course)
                .options(selectinload(Course.chapters))
                .filter(Course.id.in_(course_ids))
                .all()
            )
        summaries = CourseProgressService(self.db).get_user_course_summaries(user_id, courses)
        progress_count = sum(
            1
            for summary in summaries.values()
            if 0 < summary.progress_percent < 100
        )

        # 考试数
        exam_count = self.db.query(ExamRecord).filter(
            ExamRecord.user_id == user_id
        ).count()

        # 培训数
        enrollment_count = self.db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.status == 'approved'
        ).count()

        # 最近考试
        recent_exams = self.db.query(ExamRecord).filter(
            ExamRecord.user_id == user_id
        ).order_by(ExamRecord.end_time.desc()).limit(5).all()

        return DashboardResponse(
            stats={
                "courses_in_progress": progress_count,
                "exams_taken": exam_count,
                "trainings_enrolled": enrollment_count
            },
            recent_exams=[{
                "id": r.id, "exam_id": r.exam_id,
                "score": r.score, "result": r.result
            } for r in recent_exams]
        )
