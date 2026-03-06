"""
课程管理服务
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Course, Chapter, CourseProgress, User
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    ChapterResponse, CourseProgressUpdate, CourseProgressResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class CourseService:
    """课程服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_courses(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = None
    ) -> PaginatedResponse[CourseListResponse]:
        """获取课程列表"""
        query = self.db.query(Course).options(joinedload(Course.instructor))

        if search:
            query = query.filter(Course.title.contains(search))
        if category:
            query = query.filter(Course.category == category)

        # 排序
        if sort == "rating":
            query = query.order_by(Course.rating.desc())
        elif sort == "students":
            query = query.order_by(Course.student_count.desc())
        elif sort == "newest":
            query = query.order_by(Course.created_at.desc())
        else:
            query = query.order_by(Course.created_at.desc())

        total = query.count()

        if size == -1:
            courses = query.all()
        else:
            skip = (page - 1) * size
            courses = query.offset(skip).limit(size).all()

        items = []
        for c in courses:
            item = CourseListResponse(
                id=c.id, title=c.title, category=c.category,
                file_type=c.file_type, description=c.description,
                instructor_id=c.instructor_id,
                instructor_name=c.instructor.nickname if c.instructor else None,
                duration=c.duration, student_count=c.student_count,
                rating=c.rating, difficulty=c.difficulty,
                is_required=c.is_required, cover_color=c.cover_color,
                tags=c.tags, created_at=c.created_at
            )
            items.append(item)

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def create_course(self, data: CourseCreate, user_id: int) -> CourseResponse:
        """创建课程"""
        course = Course(
            title=data.title, category=data.category,
            file_type=data.file_type, description=data.description,
            instructor_id=data.instructor_id or user_id,
            duration=data.duration, difficulty=data.difficulty,
            is_required=data.is_required, cover_color=data.cover_color,
            tags=data.tags
        )
        self.db.add(course)
        self.db.flush()

        # 创建章节
        if data.chapters:
            for idx, ch in enumerate(data.chapters):
                chapter = Chapter(
                    course_id=course.id, title=ch.title,
                    sort_order=ch.sort_order or idx,
                    duration=ch.duration, video_url=ch.video_url,
                    doc_url=ch.doc_url
                )
                self.db.add(chapter)

        self.db.commit()
        self.db.refresh(course)
        logger.info(f"创建课程: {course.title}")
        return self._to_response(course)

    def get_course_by_id(self, course_id: int) -> Optional[CourseResponse]:
        """获取课程详情"""
        course = self.db.query(Course).options(
            joinedload(Course.instructor),
            joinedload(Course.chapters)
        ).filter(Course.id == course_id).first()

        if not course:
            return None
        return self._to_response(course)

    def update_course(self, course_id: int, data: CourseUpdate) -> Optional[CourseResponse]:
        """更新课程"""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)

        self.db.commit()
        self.db.refresh(course)
        logger.info(f"更新课程: {course.title}")
        return self._to_response(course)

    def get_user_progress(self, user_id: int) -> List[CourseProgressResponse]:
        """获取用户学习进度"""
        records = self.db.query(CourseProgress).filter(
            CourseProgress.user_id == user_id
        ).all()
        return [CourseProgressResponse.model_validate(r) for r in records]

    def update_chapter_progress(
        self, course_id: int, chapter_id: int, user_id: int, data: CourseProgressUpdate
    ) -> CourseProgressResponse:
        """更新章节学习进度"""
        record = self.db.query(CourseProgress).filter(
            CourseProgress.user_id == user_id,
            CourseProgress.course_id == course_id,
            CourseProgress.chapter_id == chapter_id
        ).first()

        if not record:
            record = CourseProgress(
                user_id=user_id, course_id=course_id,
                chapter_id=chapter_id, progress=data.progress,
                last_studied_at=datetime.now()
            )
            self.db.add(record)
        else:
            record.progress = data.progress
            record.last_studied_at = datetime.now()

        self.db.commit()
        self.db.refresh(record)
        return CourseProgressResponse.model_validate(record)

    def _to_response(self, course: Course) -> CourseResponse:
        """转换为响应"""
        chapters = []
        if hasattr(course, 'chapters') and course.chapters:
            chapters = [ChapterResponse.model_validate(ch) for ch in
                        sorted(course.chapters, key=lambda x: x.sort_order)]

        return CourseResponse(
            id=course.id, title=course.title, category=course.category,
            file_type=course.file_type, description=course.description,
            instructor_id=course.instructor_id,
            instructor_name=course.instructor.nickname if course.instructor else None,
            duration=course.duration, student_count=course.student_count,
            rating=course.rating, difficulty=course.difficulty,
            is_required=course.is_required, cover_color=course.cover_color,
            tags=course.tags, chapters=chapters,
            created_at=course.created_at, updated_at=course.updated_at
        )
