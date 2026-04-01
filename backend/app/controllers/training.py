"""
培训管理控制器
"""
from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import (
    CheckinCreate,
    CheckoutCreate,
    EnrollmentCreate,
    TrainingSkipCourseRequest,
    TrainingCourseChangeLogResponse,
    TrainingCreate,
    TrainingCheckinQrResponse,
    TrainingEvaluationCreate,
    TrainingUpdate,
    TrainingWorkflowActionRequest,
)
from app.services import TrainingService
from logger import logger


class TrainingController:
    """培训控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TrainingService(db)

    def get_trainings(
        self,
        page: int = 1,
        size: int = 10,
        training_status: Optional[str] = None,
        training_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_trainings(page, size, training_status, training_type, search, current_user_id)
        except Exception as exc:
            logger.error("获取培训列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取培训列表失败")

    def get_training_stats(self, current_user_id: Optional[int] = None):
        try:
            return self.service.get_training_stats(current_user_id)
        except Exception as exc:
            logger.error("获取培训统计异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取培训统计失败")

    def create_training(self, data: TrainingCreate, user_id: int):
        try:
            return self.service.create_training(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建培训异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建培训失败")

    def get_training_by_id(self, training_id: int, current_user_id: Optional[int] = None):
        result = self.service.get_training_by_id(training_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return result

    def update_training(self, training_id: int, data: TrainingUpdate, actor_id: Optional[int] = None):
        try:
            result = self.service.update_training(training_id, data, actor_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新培训异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新培训失败")

    def manage_training(self, training_id: int, data: TrainingUpdate, actor_id: Optional[int] = None):
        return self.update_training(training_id, data, actor_id)

    def delete_training(self, training_id: int):
        if not self.service.delete_training(training_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return True

    def publish_training(
        self,
        training_id: int,
        user_id: int,
        data: Optional[TrainingWorkflowActionRequest] = None,
    ):
        try:
            result = self.service.publish_training(training_id, user_id, data.skip_steps if data else None)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def lock_training(
        self,
        training_id: int,
        user_id: int,
        data: Optional[TrainingWorkflowActionRequest] = None,
    ):
        try:
            result = self.service.lock_training(training_id, user_id, data.skip_steps if data else None)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def start_training(
        self,
        training_id: int,
        actor_id: Optional[int] = None,
        data: Optional[TrainingWorkflowActionRequest] = None,
    ):
        try:
            result = self.service.start_training(training_id, actor_id, data.skip_steps if data else None)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def end_training(self, training_id: int, actor_id: Optional[int] = None):
        result = self.service.end_training(training_id, actor_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return result

    def get_training_students(self, training_id: int, page: int = 1, size: int = 10):
        return self.service.get_training_students(training_id, page, size)

    def get_schedule(self, training_id: int):
        return self.service.get_schedule(training_id)

    def enroll(self, training_id: int, user_id: int, data: EnrollmentCreate):
        try:
            return self.service.enroll(training_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("报名异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="报名失败")

    def get_enrollments(self, training_id: int, page: int = 1, size: int = 10, user_id: Optional[int] = None):
        return self.service.get_enrollments(training_id, page, size, user_id)

    def approve_enrollment(self, training_id: int, enrollment_id: int, reviewer_id: Optional[int] = None):
        try:
            return self.service.approve_enrollment(training_id, enrollment_id, reviewer_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def reject_enrollment(
        self,
        training_id: int,
        enrollment_id: int,
        note: Optional[str] = None,
        reviewer_id: Optional[int] = None,
    ):
        try:
            return self.service.reject_enrollment(training_id, enrollment_id, note, reviewer_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def update_roster_assignments(self, training_id: int, assignments):
        try:
            return self.service.update_roster_assignments(training_id, assignments)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def get_checkin_records(
        self,
        training_id: int,
        date_filter: Optional[date] = None,
        session_key: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        return self.service.get_checkin_records(training_id, date_filter, session_key, user_id)

    def checkin(self, training_id: int, user_id: int, data: CheckinCreate):
        try:
            return self.service.checkin(training_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("签到异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="签到失败")

    def checkout(self, training_id: int, user_id: int, data: CheckoutCreate):
        try:
            return self.service.checkout(training_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("签退异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="签退失败")

    def submit_training_evaluation(self, training_id: int, user_id: int, data: TrainingEvaluationCreate):
        try:
            return self.service.submit_training_evaluation(training_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("评课异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="评课失败")

    def get_attendance_summary(self, training_id: int, session_key: str, date_filter: Optional[date] = None):
        return self.service.get_attendance_summary(training_id, session_key, date_filter)

    def generate_checkin_qr(
        self,
        training_id: int,
        session_key: str = "start",
        date_filter: Optional[date] = None,
        user_id: Optional[int] = None,
    ) -> TrainingCheckinQrResponse:
        try:
            return self.service.generate_checkin_qr(training_id, session_key, date_filter, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def get_checkin_qr_payload(self, token: str):
        try:
            result = self.service.get_checkin_qr_payload(token)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到二维码不存在或已失效")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def checkin_by_qr(self, token: str, user_id: int):
        try:
            return self.service.checkin_by_qr(token, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def get_training_histories(self, training_id: int, user_id: Optional[int] = None):
        return self.service.get_training_histories(training_id, user_id)

    def get_training_course_change_logs(self, training_id: int) -> list[TrainingCourseChangeLogResponse]:
        return self.service.get_training_course_change_logs(training_id)

    def get_user_training_histories(self, user_id: int):
        return self.service.get_user_training_histories(user_id)

    def start_session_checkin(self, training_id: int, session_key: str, user_id: int, checkin_mode: str = "direct", checkin_duration_minutes: int = 15):
        try:
            return self.service.start_session_checkin(training_id, session_key, user_id, checkin_mode, checkin_duration_minutes)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def end_session_checkin(self, training_id: int, session_key: str, user_id: int):
        try:
            return self.service.end_session_checkin(training_id, session_key, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def start_session_checkout(self, training_id: int, session_key: str, user_id: int):
        try:
            return self.service.start_session_checkout(training_id, session_key, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def end_session_checkout(self, training_id: int, session_key: str, user_id: int):
        try:
            return self.service.end_session_checkout(training_id, session_key, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    def skip_session(self, training_id: int, session_key: str, user_id: int, data: Optional[TrainingSkipCourseRequest] = None):
        try:
            return self.service.skip_session(training_id, session_key, user_id, data.reason if data else None)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
