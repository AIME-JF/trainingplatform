"""
课程管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import CourseService
from app.schemas import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    CourseProgressUpdate, CourseProgressResponse, PaginatedResponse
)
from logger import logger


class CourseController:
    """课程控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = CourseService(db)

    def get_courses(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                    category: Optional[str] = None, sort: Optional[str] = None):
        try:
            return self.service.get_courses(page, size, search, category, sort)
        except Exception as e:
            logger.error(f"获取课程列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取课程列表失败")

    def create_course(self, data: CourseCreate, user_id: int):
        try:
            return self.service.create_course(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建课程异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建课程失败")

    def get_course_by_id(self, course_id: int):
        result = self.service.get_course_by_id(course_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
        return result

    def update_course(self, course_id: int, data: CourseUpdate):
        try:
            result = self.service.update_course(course_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新课程异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新课程失败")

    def get_user_progress(self, user_id: int):
        return self.service.get_user_progress(user_id)

    def update_chapter_progress(self, course_id: int, chapter_id: int, user_id: int, data: CourseProgressUpdate):
        try:
            return self.service.update_chapter_progress(course_id, chapter_id, user_id, data)
        except Exception as e:
            logger.error(f"更新进度异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新进度失败")
