"""
个人中心服务
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func

from app.models import User, CourseProgress, ExamRecord, Certificate, Exam, Course
from app.services.course_progress import CourseProgressService
from app.services.notice import NoticeService
from app.schemas.profile import (
    ProfileUpdate, ProfileResponse, StudyStatsResponse,
    ExamHistoryResponse, ProfileOverviewResponse
)
from logger import logger


class ProfileService:
    """个人中心服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: int) -> Optional[ProfileResponse]:
        """获取个人信息"""
        user = self.db.query(User).options(
            joinedload(User.roles),
            joinedload(User.departments),
            joinedload(User.police_types)
        ).filter(User.id == user_id).first()

        if not user:
            return None

        roles = [r.name for r in user.roles] if user.roles else []
        departments = [d.name for d in user.departments] if user.departments else []
        police_types = [pt.name for pt in user.police_types] if user.police_types else []

        return ProfileResponse(
            id=user.id, username=user.username,
            nickname=user.nickname, gender=user.gender,
            email=user.email, phone=user.phone,
            police_id=user.police_id, avatar=user.avatar,
            join_date=user.join_date, level=user.level,
            study_hours=user.study_hours or 0,
            exam_count=user.exam_count or 0,
            avg_score=user.avg_score or 0,
            roles=roles, departments=departments,
            police_types=police_types, created_at=user.created_at
        )

    def update_profile(self, user_id: int, data: ProfileUpdate) -> Optional[ProfileResponse]:
        """更新个人信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        logger.info(f"用户{user_id}更新个人信息")
        return self.get_profile(user_id)

    def get_study_stats(self, user_id: int) -> StudyStatsResponse:
        """获取学习统计"""
        # 课程统计按课程聚合，避免按章节最大值误算为整门课完成。
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
        completed = sum(1 for summary in summaries.values() if summary.progress_percent >= 100)
        in_progress = sum(1 for summary in summaries.values() if 0 < summary.progress_percent < 100)

        # 考试统计
        exam_count = self.db.query(ExamRecord).filter(
            ExamRecord.user_id == user_id
        ).count()

        avg_result = self.db.query(func.avg(ExamRecord.score)).filter(
            ExamRecord.user_id == user_id
        ).scalar() or 0

        # 证书统计
        cert_count = self.db.query(Certificate).filter(
            Certificate.user_id == user_id
        ).count()

        user = self.db.query(User).filter(User.id == user_id).first()

        return StudyStatsResponse(
            total_courses=len(summaries),
            completed_courses=completed,
            in_progress_courses=in_progress,
            total_study_hours=user.study_hours if user else 0,
            total_exams=exam_count,
            avg_score=round(float(avg_result), 1),
            certificates_count=cert_count
        )

    def get_overview(self, user_id: int) -> Optional[ProfileOverviewResponse]:
        """获取移动端个人中心概览"""
        profile = self.get_profile(user_id)
        if not profile:
            return None

        notice_service = NoticeService(self.db)
        return ProfileOverviewResponse(
            profile=profile,
            study_stats=self.get_study_stats(user_id),
            notice_unread_count=notice_service.get_unread_count(user_id),
            recent_notices=notice_service.get_recent_notifications(user_id, limit=3),
        )

    def get_exam_history(self, user_id: int) -> List[ExamHistoryResponse]:
        """获取考试历史"""
        records = self.db.query(ExamRecord).options(
            joinedload(ExamRecord.exam)
        ).filter(
            ExamRecord.user_id == user_id
        ).order_by(ExamRecord.end_time.desc()).all()

        items = []
        for r in records:
            items.append(ExamHistoryResponse(
                id=r.id, exam_id=r.exam_id,
                exam_title=r.exam.title if r.exam else None,
                score=r.score, result=r.result,
                grade=r.grade, duration=r.duration,
                end_time=r.end_time
            ))
        return items
