"""
考试管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import ExamService
from app.schemas import ExamCreate, ExamUpdate, ExamSubmit, PaginatedResponse
from logger import logger


class ExamController:
    """考试控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ExamService(db)

    def get_exams(self, page: int = 1, size: int = 10, exam_status: Optional[str] = None,
                  exam_type: Optional[str] = None, search: Optional[str] = None):
        try:
            return self.service.get_exams(page, size, exam_status, exam_type, search)
        except Exception as e:
            logger.error(f"获取考试列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试列表失败")

    def create_exam(self, data: ExamCreate, user_id: int):
        try:
            return self.service.create_exam(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建考试异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建考试失败")

    def get_exam_detail(self, exam_id: int):
        result = self.service.get_exam_detail(exam_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试不存在")
        return result

    def submit_exam(self, exam_id: int, user_id: int, data: ExamSubmit):
        try:
            return self.service.submit_exam(exam_id, user_id, data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"提交考试异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交考试失败")

    def get_exam_result(self, exam_id: int, user_id: int):
        result = self.service.get_exam_result(exam_id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试记录不存在")
        return result

    def get_exam_scores(self, exam_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_exam_scores(exam_id, page, size)
        except Exception as e:
            logger.error(f"获取成绩列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成绩列表失败")
