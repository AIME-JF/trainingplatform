"""
课程管理控制器
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import CourseService
from app.schemas import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse,
    CourseQACreate, CourseQAResponse,
    CourseTagCreate, CourseTagResponse, CourseLearningStatusResponse,
    PaginatedResponse
)
from logger import logger


class CourseController:
    """课程控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = CourseService(db)

    def get_courses(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                    category: Optional[str] = None, sort: Optional[str] = None,
                    instructor_id: Optional[int] = None, is_required: Optional[bool] = None,
                    learning_status: Optional[str] = None, file_type: Optional[str] = None,
                    created_from: Optional[datetime] = None, created_to: Optional[datetime] = None,
                    user_id: Optional[int] = None):
        try:
            return self.service.get_courses(
                page,
                size,
                search,
                category,
                sort,
                instructor_id,
                is_required=is_required,
                learning_status=learning_status,
                file_type=file_type,
                created_from=created_from,
                created_to=created_to,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"获取课程列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取课程列表失败")

    def list_course_tags(self, search: Optional[str] = None) -> List[CourseTagResponse]:
        try:
            return self.service.list_course_tags(search=search)
        except Exception as e:
            logger.error(f"获取课程标签异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取课程标签失败")

    def create_course_tag(self, data: CourseTagCreate) -> CourseTagResponse:
        try:
            return self.service.create_course_tag(data.name)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建课程标签异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建课程标签失败")

    def create_course(self, data: CourseCreate, user_id: int):
        try:
            return self.service.create_course(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建课程异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建课程失败")

    def get_course_by_id(self, course_id: int, user_id: int = None, user_permissions: Optional[List[str]] = None):
        result = self.service.get_course_by_id(course_id, user_id=user_id, user_permissions=user_permissions or [])
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
        return result

    def update_course(self, course_id: int, data: CourseUpdate, actor_user_id: Optional[int] = None):
        try:
            result = self.service.update_course(course_id, data, actor_user_id=actor_user_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
            return result
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"更新课程异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新课程失败")

    def delete_course(self, course_id: int):
        try:
            result = self.service.delete_course(course_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除课程异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除课程失败")

    def get_user_progress(self, user_id: int):
        return self.service.get_user_progress(user_id)

    def update_chapter_progress(self, course_id: int, chapter_id: int, user_id: int, data: CourseProgressUpdate):
        try:
            return self.service.update_chapter_progress(course_id, chapter_id, user_id, data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"更新进度异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新进度失败")

    def get_course_note(self, course_id: int, user_id: int) -> CourseNoteResponse:
        try:
            return self.service.get_course_note(course_id, user_id)
        except Exception as e:
            logger.error(f"获取课程笔记异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取课程笔记失败")

    def update_course_note(self, course_id: int, user_id: int, data: CourseNoteUpdate) -> CourseNoteResponse:
        try:
            return self.service.update_course_note(course_id, user_id, data)
        except Exception as e:
            logger.error(f"更新课程笔记异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新课程笔记失败")
    def get_course_qa(self, course_id: int) -> List[CourseQAResponse]:
        try:
            return self.service.get_course_qa(course_id)
        except Exception as e:
            logger.error(f"获取答疑列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取答疑列表失败")

    def create_course_qa(self, course_id: int, user_id: int, data: CourseQACreate) -> CourseQAResponse:
        try:
            return self.service.create_course_qa(course_id, user_id, data)
        except Exception as e:
            logger.error(f"创建答疑提问异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提出问题失败")

    def get_course_learning_status(
        self,
        course_id: int,
        user_id: int,
        user_permissions: Optional[List[str]] = None,
    ) -> List[CourseLearningStatusResponse]:
        try:
            result = self.service.get_course_learning_status(course_id, user_id, user_permissions or [])
            if result is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取课程学习情况异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取课程学习情况失败")
