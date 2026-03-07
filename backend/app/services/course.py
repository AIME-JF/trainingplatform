"""
课程管理服务
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, cast, String

from app.models import Course, Chapter, CourseNote, CourseProgress, User
from app.models.media import MediaFile
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    ChapterResponse, CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse
)
from app.schemas import PaginatedResponse
from config import settings
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
            query = query.outerjoin(Course.chapters).filter(
                or_(
                    Course.title.contains(search),
                    Course.description.contains(search),
                    Chapter.title.contains(search),
                    cast(Course.tags, String).contains(search)
                )
            ).distinct()
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

        total = query.order_by(None).count()

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
                    doc_url=ch.doc_url, file_id=ch.file_id
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
        course = self.db.query(Course).options(joinedload(Course.chapters)).filter(Course.id == course_id).first()
        if not course:
            return None

        update_data = data.model_dump(exclude_unset=True)
        chapters_data = update_data.pop('chapters', None)

        for field, value in update_data.items():
            setattr(course, field, value)

        if chapters_data is not None:
            normalized = []
            for idx, ch in enumerate(chapters_data):
                chapter_dict = ch.model_dump() if hasattr(ch, 'model_dump') else dict(ch)
                chapter_dict['sort_order'] = chapter_dict.get('sort_order', idx)
                normalized.append(chapter_dict)

            self.db.query(Chapter).filter(Chapter.course_id == course.id).delete()
            for ch in normalized:
                chapter = Chapter(
                    course_id=course.id,
                    title=ch.get('title'),
                    sort_order=ch.get('sort_order', 0),
                    duration=ch.get('duration', 0),
                    video_url=ch.get('video_url'),
                    doc_url=ch.get('doc_url'),
                    file_id=ch.get('file_id')
                )
                self.db.add(chapter)

        self.db.commit()
        course = self.db.query(Course).options(
            joinedload(Course.instructor),
            joinedload(Course.chapters)
        ).filter(Course.id == course_id).first()
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

    def get_course_note(self, course_id: int, user_id: int) -> CourseNoteResponse:
        """获取课程笔记"""
        note = self.db.query(CourseNote).filter(
            CourseNote.course_id == course_id,
            CourseNote.user_id == user_id
        ).first()

        if not note:
            return CourseNoteResponse(
                id=0,
                user_id=user_id,
                course_id=course_id,
                content='',
                created_at=None,
                updated_at=None
            )
        return CourseNoteResponse.model_validate(note)

    def update_course_note(self, course_id: int, user_id: int, data: CourseNoteUpdate) -> CourseNoteResponse:
        """更新课程笔记"""
        note = self.db.query(CourseNote).filter(
            CourseNote.course_id == course_id,
            CourseNote.user_id == user_id
        ).first()

        if not note:
            note = CourseNote(
                user_id=user_id,
                course_id=course_id,
                content=data.content or ''
            )
            self.db.add(note)
        else:
            note.content = data.content or ''
            note.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(note)
        return CourseNoteResponse.model_validate(note)

    def _chapter_to_response(self, ch: Chapter) -> ChapterResponse:
        """转换章节为响应，填充 file_url"""
        file_url = None
        if ch.file_id:
            media = self.db.query(MediaFile).filter(MediaFile.id == ch.file_id).first()
            if media and media.storage_path:
                base = (settings.MINIO_PUBLIC_URL or "").rstrip("/")
                bucket = (settings.MINIO_BUCKET or "").strip("/")
                path = media.storage_path.lstrip("/")
                if base and bucket and path:
                    file_url = f"{base}/{bucket}/{path}"
                else:
                    file_url = f"{settings.API_V1_STR}/media/files/{ch.file_id}"
            else:
                file_url = f"{settings.API_V1_STR}/media/files/{ch.file_id}"
        resp = ChapterResponse(
            id=ch.id, course_id=ch.course_id, title=ch.title,
            sort_order=ch.sort_order, duration=ch.duration,
            video_url=ch.video_url, doc_url=ch.doc_url,
            file_id=ch.file_id, file_url=file_url,
        )
        return resp

    def _to_response(self, course: Course) -> CourseResponse:
        """转换为响应"""
        chapters = []
        if hasattr(course, 'chapters') and course.chapters:
            chapters = [self._chapter_to_response(ch) for ch in
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
