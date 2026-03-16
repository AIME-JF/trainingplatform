"""
课程管理服务
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, func as sa_func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.course import (
    Course, Chapter, CourseNote, CourseProgress, CourseQA, CourseTag, CourseTagRelation
)
from app.models.media import MediaFile
from app.models.resource import Resource, ResourceMediaLink, CourseResourceRef, ResourceTagRelation
from app.models.user import User
from app.schemas import PaginatedResponse
from app.schemas.course import (
    ChapterResponse, CourseCreate, CourseLearningStatusResponse, CourseListResponse,
    CourseNoteResponse, CourseNoteUpdate, CourseProgressResponse, CourseProgressUpdate,
    CourseQAResponse, CourseQACreate, CourseResponse, CourseTagResponse, CourseUpdate,
)
from app.schemas.resource import CourseResourceBindRequest, ResourceListItemResponse
from app.services.auth import auth_service
from app.services.course_progress import CourseProgressService
from config import settings
from logger import logger


class CourseService:
    """课程服务"""

    LEARNING_STATUS_PERMISSION = "GET_COURSE_LEARNING_STATUS"

    def __init__(self, db: Session):
        self.db = db
        self.progress_service = CourseProgressService(db)

    def get_courses(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> PaginatedResponse[CourseListResponse]:
        """获取课程列表"""
        query = self.db.query(Course).options(
            joinedload(Course.instructor),
            selectinload(Course.chapters),
            selectinload(Course.tag_relations).joinedload(CourseTagRelation.tag),
        )

        if search:
            query = (
                query.outerjoin(Course.chapters)
                .outerjoin(Course.tag_relations)
                .outerjoin(CourseTagRelation.tag)
                .filter(
                    or_(
                        Course.title.contains(search),
                        Course.description.contains(search),
                        Chapter.title.contains(search),
                        CourseTag.name.contains(search),
                    )
                )
                .distinct()
            )
        if category:
            query = query.filter(Course.category == category)

        if sort == "rating":
            query = query.order_by(Course.rating.desc())
        elif sort == "students":
            query = query.order_by(Course.student_count.desc())
        else:
            query = query.order_by(Course.created_at.desc())

        total = query.order_by(None).count()
        if size == -1:
            courses = query.all()
        else:
            skip = (page - 1) * size
            courses = query.offset(skip).limit(size).all()

        progress_map = self.progress_service.get_user_course_summaries(user_id, courses) if user_id else {}

        items = []
        for course in courses:
            summary = progress_map.get(course.id)
            items.append(
                CourseListResponse(
                    id=course.id,
                    title=course.title,
                    category=course.category,
                    file_type=course.file_type,
                    description=course.description,
                    created_by=course.created_by,
                    instructor_id=course.instructor_id,
                    instructor_name=course.instructor.nickname if course.instructor else None,
                    duration=course.duration,
                    student_count=course.student_count,
                    rating=course.rating,
                    difficulty=course.difficulty,
                    is_required=course.is_required,
                    cover_color=course.cover_color,
                    tags=self._course_tags(course),
                    progress_percent=summary.progress_percent if summary else 0,
                    chapter_count=summary.chapter_count if summary else len(course.chapters or []),
                    completed_chapter_count=summary.completed_chapter_count if summary else 0,
                    last_studied_at=summary.last_studied_at if summary else None,
                    created_at=course.created_at,
                )
            )

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=items,
        )

    def list_course_tags(self, search: Optional[str] = None) -> List[CourseTagResponse]:
        """获取全部课程标签。"""
        query = self.db.query(CourseTag)
        keyword = str(search or "").strip()
        if keyword:
            query = query.filter(CourseTag.name.contains(keyword))
        tags = query.order_by(CourseTag.name.asc()).all()
        return [CourseTagResponse.model_validate(tag) for tag in tags]

    def create_course_tag(self, name: str) -> CourseTagResponse:
        """创建课程标签。若标签已存在则直接返回。"""
        tag = self._get_or_create_course_tag(name)
        self.db.commit()
        self.db.refresh(tag)
        return CourseTagResponse.model_validate(tag)

    def create_course(self, data: CourseCreate, user_id: int) -> CourseResponse:
        """创建课程"""
        course = Course(
            title=data.title,
            category=data.category,
            file_type=data.file_type,
            description=data.description,
            created_by=user_id,
            instructor_id=data.instructor_id,
            duration=data.duration,
            difficulty=data.difficulty,
            is_required=data.is_required,
            cover_color=data.cover_color,
        )
        self.db.add(course)
        self.db.flush()

        self._sync_course_tags(course, data.tags)
        self._upsert_course_chapters(course, data.chapters or [])

        self.db.commit()
        course = self._get_course_entity(course.id)
        logger.info(f"创建课程: {course.title}")
        return self._to_response(
            course,
            user_id=user_id,
            user_permissions=[],
        )

    def get_course_by_id(
        self,
        course_id: int,
        user_id: Optional[int] = None,
        user_permissions: Optional[List[str]] = None,
    ) -> Optional[CourseResponse]:
        """获取课程详情（含当前用户课程总进度、章节进度与权限能力）"""
        course = self._get_course_entity(course_id)
        if not course:
            return None
        return self._to_response(course, user_id=user_id, user_permissions=user_permissions or [])

    def update_course(self, course_id: int, data: CourseUpdate) -> Optional[CourseResponse]:
        """更新课程"""
        course = self._get_course_entity(course_id)
        if not course:
            return None

        update_data = data.model_dump(exclude_unset=True)
        chapters_data = update_data.pop("chapters", None)
        tags = update_data.pop("tags", None)

        for field, value in update_data.items():
            setattr(course, field, value)

        if tags is not None:
            self._sync_course_tags(course, tags)
        if chapters_data is not None:
            self._upsert_course_chapters(course, chapters_data)

        self.db.commit()
        course = self._get_course_entity(course_id)
        logger.info(f"更新课程: {course.title}")
        return self._to_response(course)

    def delete_course(self, course_id: int) -> bool:
        """删除课程及其关联的章节、笔记、进度记录"""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return False

        self.db.query(CourseProgress).filter(CourseProgress.course_id == course_id).delete()
        self.db.query(CourseNote).filter(CourseNote.course_id == course_id).delete()
        self.db.query(Chapter).filter(Chapter.course_id == course_id).delete()
        self.db.delete(course)
        self.db.commit()
        logger.info(f"课程已删除: id={course_id}, title={course.title}")
        return True

    def get_user_progress(self, user_id: int) -> List[CourseProgressResponse]:
        """获取用户学习进度明细"""
        records = self.db.query(CourseProgress).filter(CourseProgress.user_id == user_id).all()
        return [CourseProgressResponse.model_validate(record) for record in records]

    def update_chapter_progress(
        self,
        course_id: int,
        chapter_id: int,
        user_id: int,
        data: CourseProgressUpdate,
    ) -> CourseProgressResponse:
        """更新章节学习进度"""
        chapter = (
            self.db.query(Chapter)
            .filter(Chapter.id == chapter_id, Chapter.course_id == course_id)
            .first()
        )
        if not chapter:
            raise ValueError("章节不存在")

        progress = min(max(int(data.progress or 0), 0), 100)
        playback_seconds = max(int(data.playback_seconds or 0), 0)

        record = (
            self.db.query(CourseProgress)
            .filter(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id,
                CourseProgress.chapter_id == chapter_id,
            )
            .first()
        )

        if not record:
            if progress <= 0 and playback_seconds <= 0:
                return CourseProgressResponse(
                    id=0,
                    user_id=user_id,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    progress=0,
                    playback_seconds=0,
                    last_studied_at=None,
                )
            record = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                progress=progress,
                playback_seconds=playback_seconds,
                last_studied_at=datetime.now(),
            )
            self.db.add(record)
        else:
            record.progress = max(int(record.progress or 0), progress)
            record.playback_seconds = playback_seconds
            record.last_studied_at = datetime.now()

        self._refresh_student_count(course_id)
        self.db.commit()
        self.db.refresh(record)
        return CourseProgressResponse.model_validate(record)

    def get_course_note(self, course_id: int, user_id: int) -> CourseNoteResponse:
        """获取课程笔记"""
        note = (
            self.db.query(CourseNote)
            .filter(CourseNote.course_id == course_id, CourseNote.user_id == user_id)
            .first()
        )
        if not note:
            return CourseNoteResponse(
                id=0,
                user_id=user_id,
                course_id=course_id,
                content="",
                created_at=None,
                updated_at=None,
            )
        return CourseNoteResponse.model_validate(note)

    def update_course_note(self, course_id: int, user_id: int, data: CourseNoteUpdate) -> CourseNoteResponse:
        """更新课程笔记"""
        note = (
            self.db.query(CourseNote)
            .filter(CourseNote.course_id == course_id, CourseNote.user_id == user_id)
            .first()
        )

        if not note:
            note = CourseNote(user_id=user_id, course_id=course_id, content=data.content or "")
            self.db.add(note)
        else:
            note.content = data.content or ""
            note.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(note)
        return CourseNoteResponse.model_validate(note)

    def get_course_learning_status(
        self,
        course_id: int,
        user_id: int,
        user_permissions: Optional[List[str]] = None,
    ) -> Optional[List[CourseLearningStatusResponse]]:
        """获取课程学习情况。"""
        course = self._get_course_entity(course_id)
        if not course or not self._can_view_learning_status(course, user_id, user_permissions or []):
            return None

        items = self.progress_service.get_course_learning_status(course)
        return [CourseLearningStatusResponse(**item) for item in items]

    def add_course_resource(self, course_id: int, data: CourseResourceBindRequest) -> ResourceListItemResponse:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        resource = self.db.query(Resource).options(
            joinedload(Resource.uploader),
            joinedload(Resource.owner_department),
            joinedload(Resource.cover_media),
            joinedload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(Resource.id == data.resource_id).first()
        if not resource:
            raise ValueError("资源不存在")

        ref = self.db.query(CourseResourceRef).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.resource_id == data.resource_id,
        ).first()

        if not ref:
            ref = CourseResourceRef(
                course_id=course_id,
                resource_id=data.resource_id,
                usage_type=data.usage_type,
                sort_order=data.sort_order,
            )
            self.db.add(ref)
        else:
            ref.usage_type = data.usage_type
            ref.sort_order = data.sort_order

        self.db.commit()
        tags = [rel.tag.name for rel in (resource.tag_relations or []) if rel.tag]
        return ResourceListItemResponse(
            id=resource.id,
            title=resource.title,
            summary=resource.summary,
            content_type=resource.content_type,
            source_type=resource.source_type,
            status=resource.status,
            visibility_type=resource.visibility_type,
            uploader_id=resource.uploader_id,
            uploader_name=resource.uploader.nickname if resource.uploader else None,
            owner_department_id=resource.owner_department_id,
            owner_department_name=resource.owner_department.name if resource.owner_department else None,
            cover_media_file_id=resource.cover_media_file_id,
            cover_url=None,
            tags=tags,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )

    def list_course_resources(self, course_id: int) -> List[ResourceListItemResponse]:
        refs = (
            self.db.query(CourseResourceRef)
            .options(
                joinedload(CourseResourceRef.resource).joinedload(Resource.uploader),
                joinedload(CourseResourceRef.resource).joinedload(Resource.owner_department),
                joinedload(CourseResourceRef.resource).joinedload(Resource.cover_media),
                joinedload(CourseResourceRef.resource)
                .selectinload(Resource.tag_relations)
                .joinedload(ResourceTagRelation.tag),
            )
            .filter(CourseResourceRef.course_id == course_id)
            .order_by(CourseResourceRef.sort_order.asc(), CourseResourceRef.id.asc())
            .all()
        )

        items = []
        for ref in refs:
            resource = ref.resource
            if not resource:
                continue
            tags = [rel.tag.name for rel in (resource.tag_relations or []) if rel.tag]
            items.append(
                ResourceListItemResponse(
                    id=resource.id,
                    title=resource.title,
                    summary=resource.summary,
                    content_type=resource.content_type,
                    source_type=resource.source_type,
                    status=resource.status,
                    visibility_type=resource.visibility_type,
                    uploader_id=resource.uploader_id,
                    uploader_name=resource.uploader.nickname if resource.uploader else None,
                    owner_department_id=resource.owner_department_id,
                    owner_department_name=resource.owner_department.name if resource.owner_department else None,
                    cover_media_file_id=resource.cover_media_file_id,
                    cover_url=None,
                    tags=tags,
                    created_at=resource.created_at,
                    updated_at=resource.updated_at,
                )
            )
        return items

    def remove_course_resource(self, course_id: int, resource_id: int) -> bool:
        ref = self.db.query(CourseResourceRef).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.resource_id == resource_id,
        ).first()
        if not ref:
            return False
        self.db.delete(ref)
        self.db.commit()
        return True

    def get_course_qa(self, course_id: int) -> List[CourseQAResponse]:
        """获取课程答疑列表"""
        qa_list = (
            self.db.query(CourseQA)
            .options(joinedload(CourseQA.user))
            .filter(CourseQA.course_id == course_id)
            .order_by(CourseQA.created_at.desc())
            .all()
        )

        return [
            CourseQAResponse(
                id=qa.id,
                user_id=qa.user_id,
                user_name=qa.user.nickname if qa.user else "未知用户",
                course_id=qa.course_id,
                question=qa.question,
                answer=qa.answer,
                created_at=qa.created_at,
                updated_at=qa.updated_at,
            )
            for qa in qa_list
        ]

    def create_course_qa(self, course_id: int, user_id: int, data: CourseQACreate) -> CourseQAResponse:
        """创建课程提问"""
        qa = CourseQA(user_id=user_id, course_id=course_id, question=data.question)
        self.db.add(qa)
        self.db.commit()
        self.db.refresh(qa)

        user = self.db.query(User).filter(User.id == user_id).first()
        return CourseQAResponse(
            id=qa.id,
            user_id=qa.user_id,
            user_name=user.nickname if user else "我",
            course_id=qa.course_id,
            question=qa.question,
            answer=qa.answer,
            created_at=qa.created_at,
            updated_at=qa.updated_at,
        )

    def _get_course_entity(self, course_id: int) -> Optional[Course]:
        return (
            self.db.query(Course)
            .options(
                joinedload(Course.creator),
                joinedload(Course.instructor),
                selectinload(Course.chapters),
                selectinload(Course.tag_relations).joinedload(CourseTagRelation.tag),
            )
            .filter(Course.id == course_id)
            .first()
        )

    def _sync_course_tags(self, course: Course, tag_names: Optional[List[str]]) -> None:
        if tag_names is None:
            return

        normalized_names = []
        seen = set()
        for raw_name in tag_names:
            name = self._normalize_tag_name(raw_name)
            if not name or name in seen:
                continue
            seen.add(name)
            normalized_names.append(name)

        existing_relations = {
            relation.tag.name: relation
            for relation in (course.tag_relations or [])
            if relation.tag
        }
        keep_names = set(normalized_names)

        for name, relation in existing_relations.items():
            if name not in keep_names:
                self.db.delete(relation)

        for name in normalized_names:
            if name in existing_relations:
                continue
            tag = self._get_or_create_course_tag(name)
            self.db.add(CourseTagRelation(course_id=course.id, tag_id=tag.id))

    def _normalize_tag_name(self, raw_name: Optional[str]) -> str:
        return str(raw_name or "").strip()

    def _get_or_create_course_tag(self, raw_name: Optional[str]) -> CourseTag:
        name = self._normalize_tag_name(raw_name)
        if not name:
            raise ValueError("标签名称不能为空")
        if len(name) > 50:
            raise ValueError("标签名称长度不能超过50个字符")

        tag = self.db.query(CourseTag).filter(CourseTag.name == name).first()
        if tag:
            return tag

        tag = CourseTag(name=name)
        self.db.add(tag)
        self.db.flush()
        return tag

    def _upsert_course_chapters(self, course: Course, chapters_data: List[dict]) -> None:
        existing_by_id = {chapter.id: chapter for chapter in (course.chapters or []) if chapter.id is not None}
        keep_ids = set()
        active_chapters = []

        for idx, raw in enumerate(chapters_data):
            chapter_data = raw.model_dump(exclude_unset=True) if hasattr(raw, "model_dump") else dict(raw)
            chapter_id = chapter_data.get("id")
            if chapter_id is not None and chapter_id not in existing_by_id:
                raise ValueError("章节不存在")

            chapter = existing_by_id.get(chapter_id)
            if not chapter:
                chapter = Chapter(course_id=course.id)
                self.db.add(chapter)

            chapter_title = chapter_data.get("title", chapter.title)
            if chapter_title is None or not str(chapter_title).strip():
                raise ValueError(f"第{idx + 1}章标题不能为空")

            chapter.title = str(chapter_title).strip()
            chapter.sort_order = chapter_data.get("sort_order", idx)
            chapter.duration = chapter_data.get("duration", 0) or 0
            chapter.video_url = chapter_data.get("video_url", chapter.video_url)
            chapter.doc_url = chapter_data.get("doc_url", chapter.doc_url)
            chapter.file_id = chapter_data.get("file_id", chapter.file_id)
            chapter.resource_id = chapter_data.get("resource_id", chapter.resource_id)

            if chapter.id is not None:
                keep_ids.add(chapter.id)
            active_chapters.append(chapter)

        for chapter_id, chapter in existing_by_id.items():
            if chapter_id in keep_ids:
                continue
            self.db.query(CourseProgress).filter(
                CourseProgress.course_id == course.id,
                CourseProgress.chapter_id == chapter_id,
            ).delete()
            self.db.delete(chapter)

        self.db.flush()
        course.duration = sum(max(int((chapter.duration or 0)), 0) for chapter in active_chapters)
        self._refresh_student_count(course.id)

    def _refresh_student_count(self, course_id: int) -> None:
        real_count = (
            self.db.query(sa_func.count(sa_func.distinct(CourseProgress.user_id)))
            .filter(
                CourseProgress.course_id == course_id,
                or_(CourseProgress.progress > 0, CourseProgress.playback_seconds > 0),
            )
            .scalar()
            or 0
        )
        self.db.query(Course).filter(Course.id == course_id).update({"student_count": real_count})
        self.db.flush()

    def _course_tags(self, course: Course) -> List[str]:
        return [rel.tag.name for rel in (course.tag_relations or []) if rel.tag]

    def _can_view_learning_status(
        self,
        course: Course,
        user_id: int,
        user_permissions: List[str],
    ) -> bool:
        if user_id == course.created_by:
            return True
        if user_id == course.instructor_id:
            return True
        return auth_service.check_permission(user_permissions, self.LEARNING_STATUS_PERMISSION)

    def _resolve_file_url(self, media_id: int, storage_path: Optional[str]) -> str:
        if storage_path:
            base = (settings.MINIO_PUBLIC_URL or "").rstrip("/")
            bucket = (settings.MINIO_BUCKET or "").strip("/")
            path = storage_path.lstrip("/")
            if base and bucket and path:
                return f"{base}/{bucket}/{path}"
        return f"{settings.API_V1_STR}/media/files/{media_id}"

    def _guess_content_type(
        self,
        filename_or_url: Optional[str],
        mime_type: Optional[str] = None,
    ) -> Optional[str]:
        source = (filename_or_url or "").lower()
        mime = (mime_type or "").lower()
        if "video" in mime or source.endswith(".mp4"):
            return "video"
        if "pdf" in mime or any(source.endswith(ext) for ext in (".pdf", ".ppt", ".pptx", ".doc", ".docx")):
            return "document"
        return None

    def _chapter_to_response(
        self,
        chapter: Chapter,
        progress_summary=None,
    ) -> ChapterResponse:
        """转换章节为响应，填充 file_url、类型和用户进度"""
        file_url = None
        content_type = None

        if getattr(chapter, "resource_id", None):
            resource = self.db.query(Resource).options(
                joinedload(Resource.media_links).joinedload(ResourceMediaLink.media_file)
            ).filter(Resource.id == chapter.resource_id).first()
            if resource and resource.status == "published":
                links = sorted((resource.media_links or []), key=lambda item: item.sort_order)
                main_link = next((item for item in links if item.media_role == "main"), None) or (links[0] if links else None)
                media = main_link.media_file if main_link else None
                if media:
                    file_url = self._resolve_file_url(media.id, media.storage_path)
                    content_type = self._guess_content_type(media.filename, media.mime_type) or resource.content_type

        if not file_url and chapter.file_id:
            media = self.db.query(MediaFile).filter(MediaFile.id == chapter.file_id).first()
            if media:
                file_url = self._resolve_file_url(media.id, media.storage_path)
                content_type = self._guess_content_type(media.filename, media.mime_type)
            else:
                file_url = f"{settings.API_V1_STR}/media/files/{chapter.file_id}"

        if not content_type:
            content_type = (
                self._guess_content_type(chapter.video_url)
                or self._guess_content_type(chapter.doc_url)
                or "video"
            )

        progress_record = None
        if progress_summary:
            progress_record = progress_summary.chapter_records.get(chapter.id)

        return ChapterResponse(
            id=chapter.id,
            course_id=chapter.course_id,
            title=chapter.title,
            sort_order=chapter.sort_order,
            duration=chapter.duration,
            video_url=chapter.video_url,
            doc_url=chapter.doc_url,
            file_id=chapter.file_id,
            resource_id=getattr(chapter, "resource_id", None),
            file_url=file_url,
            content_type=content_type,
            progress=progress_record.progress if progress_record else 0,
            playback_seconds=int(progress_record.playback_seconds or 0) if progress_record else 0,
            last_studied_at=progress_record.last_studied_at if progress_record else None,
        )

    def _to_response(
        self,
        course: Course,
        user_id: Optional[int] = None,
        user_permissions: Optional[List[str]] = None,
    ) -> CourseResponse:
        """转换为响应，注入课程总进度与权限信息。"""
        user_permissions = user_permissions or []
        sorted_chapters = sorted(course.chapters or [], key=lambda item: item.sort_order)
        progress_summary = None
        if user_id:
            progress_summary = self.progress_service.get_user_course_summaries(user_id, [course]).get(course.id)

        chapters = [self._chapter_to_response(chapter, progress_summary) for chapter in sorted_chapters]
        note = self.get_course_note(course.id, user_id) if user_id else None
        qa_list = self.get_course_qa(course.id)
        resources = self.list_course_resources(course.id)

        return CourseResponse(
            id=course.id,
            title=course.title,
            category=course.category,
            file_type=course.file_type,
            description=course.description,
            created_by=course.created_by,
            created_by_name=course.creator.nickname if course.creator else None,
            instructor_id=course.instructor_id,
            instructor_name=course.instructor.nickname if course.instructor else None,
            duration=course.duration,
            student_count=course.student_count,
            rating=course.rating,
            difficulty=course.difficulty,
            is_required=course.is_required,
            cover_color=course.cover_color,
            tags=self._course_tags(course),
            progress_percent=progress_summary.progress_percent if progress_summary else 0,
            chapter_count=progress_summary.chapter_count if progress_summary else len(sorted_chapters),
            completed_chapter_count=progress_summary.completed_chapter_count if progress_summary else 0,
            last_studied_at=progress_summary.last_studied_at if progress_summary else None,
            last_studied_chapter_id=progress_summary.last_studied_chapter_id if progress_summary else None,
            last_studied_chapter_title=progress_summary.last_studied_chapter_title if progress_summary else None,
            last_playback_seconds=progress_summary.last_playback_seconds if progress_summary else 0,
            can_view_learning_status=(
                self._can_view_learning_status(course, user_id, user_permissions)
                if user_id
                else False
            ),
            chapters=chapters,
            note=note,
            qa_list=qa_list,
            resources=resources,
            created_at=course.created_at,
            updated_at=course.updated_at,
        )
