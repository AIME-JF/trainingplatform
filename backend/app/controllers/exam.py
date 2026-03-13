"""
考试管理控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import AdmissionExamCreate, AdmissionExamUpdate, ExamCreate, ExamSubmit, ExamUpdate
from app.services import ExamService
from logger import logger


class ExamController:
    """考试控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ExamService(db)

    def get_exams(
        self,
        page: int = 1,
        size: int = 10,
        exam_status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        training_id: Optional[int] = None,
        purpose: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_exams(
                page,
                size,
                exam_status,
                exam_type,
                search,
                training_id,
                purpose,
                current_user_id,
            )
        except Exception as exc:
            logger.error("获取培训班内考试列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试列表失败")

    def get_admission_exams(
        self,
        page: int = 1,
        size: int = 10,
        exam_status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_admission_exams(page, size, exam_status, exam_type, search, current_user_id)
        except Exception as exc:
            logger.error("获取准入考试列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取准入考试列表失败")

    def create_exam(self, data: ExamCreate, user_id: int):
        try:
            return self.service.create_exam(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建考试失败")

    def create_admission_exam(self, data: AdmissionExamCreate, user_id: int):
        try:
            return self.service.create_admission_exam(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建准入考试失败")

    def update_exam(self, exam_id: int, data: ExamUpdate):
        try:
            return self.service.update_exam(exam_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新考试失败")

    def update_admission_exam(self, exam_id: int, data: AdmissionExamUpdate):
        try:
            return self.service.update_admission_exam(exam_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新准入考试失败")

    def get_exam_detail(self, exam_id: int):
        result = self.service.get_exam_detail(exam_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试不存在")
        return result

    def get_admission_exam_detail(self, exam_id: int):
        result = self.service.get_admission_exam_detail(exam_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="准入考试不存在")
        return result

    def submit_exam(self, exam_id: int, user_id: int, data: ExamSubmit):
        try:
            return self.service.submit_exam(exam_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("提交培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交考试失败")

    def submit_admission_exam(self, exam_id: int, user_id: int, data: ExamSubmit):
        try:
            return self.service.submit_admission_exam(exam_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("提交准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交准入考试失败")

    def get_exam_result(self, exam_id: int, user_id: int):
        result = self.service.get_exam_result(exam_id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试记录不存在")
        return result

    def get_admission_exam_result(self, exam_id: int, user_id: int):
        result = self.service.get_admission_exam_result(exam_id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试记录不存在")
        return result

    def get_exam_scores(self, exam_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_exam_scores(exam_id, page, size)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取培训班内考试成绩异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成绩列表失败")

    def get_admission_exam_scores(self, exam_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_admission_exam_scores(exam_id, page, size)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取准入考试成绩异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成绩列表失败")

    def get_exam_analysis(self, exam_id: int):
        try:
            return self.service.get_exam_analysis(exam_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取培训班内考试分析异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试分析数据失败")

    def get_admission_exam_analysis(self, exam_id: int):
        try:
            return self.service.get_admission_exam_analysis(exam_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取准入考试分析异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试分析数据失败")
