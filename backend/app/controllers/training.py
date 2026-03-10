"""
培训管理控制器
"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import TrainingService
from app.schemas import (
    TrainingCreate, TrainingUpdate, EnrollmentCreate, CheckinCreate, PaginatedResponse
)
from logger import logger


class TrainingController:
    """培训控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TrainingService(db)

    def get_trainings(self, page: int = 1, size: int = 10, training_status: Optional[str] = None,
                      training_type: Optional[str] = None, search: Optional[str] = None):
        try:
            return self.service.get_trainings(page, size, training_status, training_type, search)
        except Exception as e:
            logger.error(f"获取培训列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取培训列表失败")

    def create_training(self, data: TrainingCreate, user_id: int):
        try:
            return self.service.create_training(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建培训异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建培训失败")

    def get_training_by_id(self, training_id: int):
        result = self.service.get_training_by_id(training_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return result

    def update_training(self, training_id: int, data: TrainingUpdate):
        try:
            result = self.service.update_training(training_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新培训异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新培训失败")

    def delete_training(self, training_id: int):
        if not self.service.delete_training(training_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return True

    def start_training(self, training_id: int):
        result = self.service.start_training(training_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
        return result

    def end_training(self, training_id: int):
        result = self.service.end_training(training_id)
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
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"报名异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="报名失败")

    def get_enrollments(self, training_id: int, page: int = 1, size: int = 10):
        return self.service.get_enrollments(training_id, page, size)

    def approve_enrollment(self, training_id: int, enrollment_id: int):
        try:
            return self.service.approve_enrollment(training_id, enrollment_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def reject_enrollment(self, training_id: int, enrollment_id: int, note: Optional[str] = None):
        try:
            return self.service.reject_enrollment(training_id, enrollment_id, note)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_checkin_records(self, training_id: int, date_filter: Optional[date] = None):
        return self.service.get_checkin_records(training_id, date_filter)

    def checkin(self, training_id: int, user_id: int, data: CheckinCreate):
        try:
            return self.service.checkin(training_id, user_id, data)
        except Exception as e:
            logger.error(f"签到异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="签到失败")

    def generate_checkin_qr(self, training_id: int):
        return self.service.generate_checkin_qr(training_id)
