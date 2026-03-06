"""
教官管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import InstructorService
from app.schemas import InstructorProfileCreate, PaginatedResponse
from logger import logger


class InstructorController:
    """教官控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = InstructorService(db)

    def get_instructors(self, page: int = 1, size: int = 10,
                        search: Optional[str] = None, specialty: Optional[str] = None):
        try:
            return self.service.get_instructors(page, size, search, specialty)
        except Exception as e:
            logger.error(f"获取教官列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取教官列表失败")

    def get_instructor_by_id(self, instructor_id: int):
        result = self.service.get_instructor_by_id(instructor_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教官不存在")
        return result

    def create_instructor(self, data: InstructorProfileCreate):
        try:
            return self.service.create_instructor(data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建教官异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建教官失败")
