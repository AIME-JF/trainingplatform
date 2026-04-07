"""
课程管理服务
"""

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import or_, func as sa_func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.course import (
    Course, Chapter, CourseNote, CourseProgress, CourseQA, CourseTag, CourseTagRelation
)
from app.models.department import Department
from app.models.library import LibraryItem
from app.models.media import MediaFile
from app.models.resource import Resource, ResourceMediaLink, CourseResourceRef, ResourceTagRelation
from app.models.role import Role
from app.models.training import Training, TrainingCourse
from app.models.user import User
from app.schemas import PaginatedResponse
from app.schemas.course import (
    ChapterResponse, CourseCreate, CourseLearningStatusResponse, CourseListResponse,
    CourseNoteResponse, CourseNoteUpdate, CourseProgressResponse, CourseProgressUpdate,
    CourseQAResponse, CourseQACreate, CourseRelatedTrainingResponse, CourseResponse, CourseTagResponse, CourseUpdate,
)
from app.schemas.exam import (
    ADMISSION_SCOPE_ALL,
    ADMISSION_SCOPE_DEPARTMENT,
    ADMISSION_SCOPE_ROLE,
    ADMISSION_SCOPE_USER,
)
from app.schemas.resource import CourseBoundResourceResponse, CourseResourceBindRequest
from app.services.auth import auth_service
from app.services.course_progress import CourseProgressService
from app.utils.data_scope import DataScopeContext, build_data_scope_context, can_access_scoped_object
from config import settings
from logger import logger


class CourseService:
    """课程服务"""

    LEARNING_STATUS_PERMISSION = "GET_COURSE_LEARNING_STATUS"

    def __init__(self, db: Session):
        self.db = db
        self.progress_service = CourseProgressService(db)

    def get_course_entity(self, course_id: int) -> Optional[Course]:
        """公开的课程实体读取，用于路由侧做权限判断。"""
        return self._get_course_entity(course_id)

    def can_view_course(self, course: Optional[Course], user_id: Optional[int]) -> bool:
        """判断用户是否可查看课程。"""
        if not course or not user_id:
            return False
        current_user = self._get_scope_user(user_id)
        scope_context = build_data_scope_context(self.db, user_id)
        return self._can_view_course(course, current_user, scope_context)

    def can_manage_course(self, course: Optional[Course], user_id: Optional[int]) -> bool:
        """判断用户是否可管理课程。"""
        if not course or not user_id:
            return False
        current_user = self._get_scope_user(user_id)
        return self._can_manage_course(course, current_user)

    def get_courses(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = None,
        instructor_id: Optional[int] = None,
        is_required: Optional[bool] = None,
        learning_status: Optional[str] = None,
        file_type: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ) -> PaginatedResponse[CourseListResponse]:
        """获取课程列表"""
        query = self.db.query(Course).options(
            joinedload(Course.creator),
            joinedload(Course.instructor),
            selectinload(Course.chapters).joinedload(Chapter.file),
            selectinload(Course.chapters).joinedload(Chapter.library_item).joinedload(LibraryItem.media_file),
            selectinload(Course.chapters).joinedload(Chapter.resource)
            .selectinload(Resource.media_links)
            .joinedload(ResourceMediaLink.media_file),
            selectinload(Course.tag_relations).joinedload(CourseTagRelation.tag),
        )

        keyword = str(search or "").strip()
        if keyword:
            query = query.filter(
                or_(
                    Course.title.contains(keyword),
                    Course.description.contains(keyword),
                    Course.chapters.any(Chapter.title.contains(keyword)),
                    Course.tag_relations.any(
                        CourseTagRelation.tag.has(CourseTag.name.contains(keyword))
                    ),
                )
            )
        if category:
            query = query.filter(Course.category == category)
        if instructor_id is not None:
            query = query.filter(Course.instructor_id == instructor_id)
        if is_required is not None:
            query = query.filter(Course.is_required == is_required)
        if file_type:
            query = query.filter(Course.file_type == file_type)
        if created_from:
            query = query.filter(Course.created_at >= created_from)
        if created_to:
            query = query.filter(Course.created_at <= created_to)
        query = query.order_by(Course.created_at.desc(), Course.id.desc())

        current_user = self._get_scope_user(user_id) if user_id else None
        if user_id and not current_user:
            return PaginatedResponse(page=page, size=0 if size == -1 else size, total=0, items=[])
        can_manage_all = self._is_admin_user(current_user)
        scope_context = build_data_scope_context(self.db, user_id) if user_id else None
        courses = query.all()
        if current_user and not can_manage_all:
            courses = [course for course in courses if self._can_view_course(course, current_user, scope_context)]

        progress_map = self.progress_service.get_user_course_summaries(user_id, courses) if user_id and courses else {}
        resolved_sort = str(sort or "").strip()
        if not resolved_sort:
            resolved_sort = "learning_priority" if self._has_role(current_user, "student") else "latest"

        items = []
        for course in courses:
            summary = progress_map.get(course.id)
            resolved_progress_percent = summary.progress_percent if summary else 0
            resolved_chapter_count = summary.chapter_count if summary else len(course.chapters or [])
            resolved_completed_chapter_count = summary.completed_chapter_count if summary else 0
            resolved_duration_seconds = self._resolve_course_duration_seconds(course)
            has_learning_activity = bool(
                summary and (
                    summary.last_studied_at
                    or summary.last_playback_seconds > 0
                    or any(
                        (record.progress or 0) > 0 or (record.playback_seconds or 0) > 0
                        for record in summary.chapter_records.values()
                    )
                )
            )
            items.append(
                CourseListResponse(
                    id=course.id,
                    title=course.title,
                    category=course.category,
                    file_type=self._resolve_course_file_type_for_response(course, course.chapters or []),
                    description=course.description,
                    created_by=course.created_by,
                    instructor_id=course.instructor_id,
                    instructor_name=course.instructor.nickname if course.instructor else None,
                    duration=self._minutes_from_seconds(resolved_duration_seconds, fallback_minutes=course.duration),
                    duration_seconds=resolved_duration_seconds,
                    student_count=course.student_count,
                    rating=course.rating,
                    difficulty=course.difficulty,
                    is_required=course.is_required,
                    cover_color=course.cover_color,
                    scope=course.scope,
                    scope_type=course.scope_type or ADMISSION_SCOPE_ALL,
                    scope_target_ids=self._normalize_scope_target_ids(course.scope_target_ids),
                    tags=self._course_tags(course),
                    progress_percent=resolved_progress_percent,
                    learning_status=self._resolve_learning_status(
                        resolved_progress_percent,
                        resolved_chapter_count,
                        resolved_completed_chapter_count,
                        has_learning_activity,
                    ),
                    chapter_count=resolved_chapter_count,
                    completed_chapter_count=resolved_completed_chapter_count,
                    last_studied_at=summary.last_studied_at if summary else None,
                    can_manage_course=self._can_manage_course(course, current_user),
                    created_at=course.created_at,
                )
            )

        if learning_status:
            items = [item for item in items if item.learning_status == learning_status]

        items.sort(key=lambda item: self._build_course_sort_key(item, resolved_sort))

        total = len(items)
        if size != -1:
            skip = (page - 1) * size
            items = items[skip: skip + size]

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
        scope_type, scope_target_ids, scope_summary = self._prepare_course_scope(
            data.scope_type,
            data.scope_target_ids,
        )
        course = Course(
            title=data.title,
            category=data.category,
            file_type=data.file_type,
            description=data.description,
            created_by=user_id,
            instructor_id=data.instructor_id,
            duration=0,
            difficulty=self._normalize_course_difficulty(getattr(data, "difficulty", None)),
            is_required=data.is_required,
            cover_color=data.cover_color,
            scope=scope_summary,
            scope_type=scope_type,
            scope_target_ids=scope_target_ids,
        )
        self.db.add(course)
        self.db.flush()

        self._sync_course_tags(course, data.tags)
        self._upsert_course_chapters(course, data.chapters or [], actor_user_id=user_id)
        self._sync_course_shell_state(
            course,
            preferred_file_type=data.file_type,
            infer_from_chapters=bool(data.chapters),
        )

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
        current_user = self._get_scope_user(user_id) if user_id else None
        if user_id and not current_user:
            return None
        if current_user and not self._is_admin_user(current_user):
            if not self._can_view_course(course, current_user):
                return None
        return self._to_response(course, user_id=user_id, user_permissions=user_permissions or [])

    def update_course(self, course_id: int, data: CourseUpdate, actor_user_id: Optional[int] = None) -> Optional[CourseResponse]:
        """更新课程"""
        course = self._get_course_entity(course_id)
        if not course:
            return None

        update_data = data.model_dump(exclude_unset=True)
        chapters_data = update_data.pop("chapters", None)
        tags = update_data.pop("tags", None)
        next_scope_type = update_data.pop("scope_type", course.scope_type or ADMISSION_SCOPE_ALL)
        next_scope_target_ids = update_data.pop("scope_target_ids", course.scope_target_ids or [])
        update_data.pop("scope", None)
        if "difficulty" in update_data:
            update_data["difficulty"] = self._normalize_course_difficulty(
                update_data.get("difficulty"),
                default=course.difficulty or 1,
            )

        for field, value in update_data.items():
            setattr(course, field, value)

        scope_type, scope_target_ids, scope_summary = self._prepare_course_scope(
            next_scope_type,
            next_scope_target_ids,
        )
        course.scope_type = scope_type
        course.scope_target_ids = scope_target_ids
        course.scope = scope_summary

        if tags is not None:
            self._sync_course_tags(course, tags)
        if chapters_data is not None:
            self._upsert_course_chapters(course, chapters_data, actor_user_id=actor_user_id)
        self._sync_course_shell_state(
            course,
            preferred_file_type=update_data.get("file_type"),
            infer_from_chapters=chapters_data is not None,
        )

        self.db.commit()
        course = self._get_course_entity(course_id)
        logger.info(f"更新课程: {course.title}")
        return self._to_response(course, user_id=actor_user_id)

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
        current_user = self._get_scope_user(user_id)
        if not current_user:
            return []
        if not self._is_admin_user(current_user) and records:
            course_ids = {record.course_id for record in records if record.course_id}
            courses = self.db.query(Course).filter(Course.id.in_(course_ids)).all() if course_ids else []
            course_map = {course.id: course for course in courses}
            records = [
                record
                for record in records
                if self._can_view_course(course_map.get(record.course_id), current_user)
            ]
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

    def list_related_trainings(
        self,
        course_id: int,
        current_user_id: int,
        current_user: Optional[User] = None,
    ) -> List[CourseRelatedTrainingResponse]:
        user = current_user or self._get_scope_user(current_user_id)
        if not user or not user.is_active:
            return []

        training_courses = (
            self.db.query(TrainingCourse)
            .options(
                joinedload(TrainingCourse.training).joinedload(Training.instructor),
            )
            .filter(TrainingCourse.course_id == course_id)
            .order_by(TrainingCourse.id.desc())
            .all()
        )

        grouped: dict[int, CourseRelatedTrainingResponse] = {}
        is_admin = self._is_admin_user(user)
        for training_course in training_courses:
            training = training_course.training
            if not training:
                continue

            relation_roles = self._resolve_training_relation_roles(
                training,
                training_course,
                current_user_id,
                is_admin=is_admin,
            )
            if not relation_roles:
                continue

            existing = grouped.get(training.id)
            if existing:
                existing.relation_roles = list(dict.fromkeys([*existing.relation_roles, *relation_roles]))
                continue

            grouped[training.id] = CourseRelatedTrainingResponse(
                id=training.id,
                name=training.name,
                class_code=training.class_code,
                status=training.status or "upcoming",
                start_date=training.start_date,
                end_date=training.end_date,
                instructor_name=training.instructor.nickname if training.instructor else None,
                relation_roles=relation_roles,
            )

        return sorted(
            grouped.values(),
            key=lambda item: (
                item.start_date or datetime.min.date(),
                item.id,
            ),
            reverse=True,
        )

    def add_course_resource(
        self,
        course_id: int,
        data: CourseResourceBindRequest,
        actor_user_id: Optional[int] = None,
    ) -> CourseBoundResourceResponse:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        actor_user = self._get_scope_user(actor_user_id) if actor_user_id else None
        is_admin = self._is_admin_user(actor_user)
        ref = None

        if data.library_item_id is not None:
            library_item = self.db.query(LibraryItem).options(
                joinedload(LibraryItem.media_file),
                joinedload(LibraryItem.owner).selectinload(User.departments),
            ).filter(LibraryItem.id == data.library_item_id).first()
            if not library_item:
                raise ValueError("资源库资源不存在")

            if actor_user_id and actor_user and not is_admin and library_item.owner_user_id != actor_user_id:
                raise ValueError("只能关联当前用户自己的资源库资源")

            ref = self.db.query(CourseResourceRef).filter(
                CourseResourceRef.course_id == course_id,
                CourseResourceRef.library_item_id == data.library_item_id,
            ).first()

            if not ref:
                ref = CourseResourceRef(
                    course_id=course_id,
                    resource_id=None,
                    library_item_id=data.library_item_id,
                    usage_type=data.usage_type,
                    sort_order=data.sort_order,
                )
                self.db.add(ref)
            else:
                ref.usage_type = data.usage_type
                ref.sort_order = data.sort_order
        else:
            resource = self.db.query(Resource).options(
                joinedload(Resource.uploader),
                joinedload(Resource.owner_department),
                joinedload(Resource.cover_media),
                joinedload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
                selectinload(Resource.media_links).joinedload(ResourceMediaLink.media_file),
            ).filter(Resource.id == data.resource_id).first()
            if not resource:
                raise ValueError("资源不存在")

            if actor_user_id and actor_user and not is_admin:
                if resource.uploader_id != actor_user_id:
                    raise ValueError("只能关联当前用户自己上传的已发布资源")
                if resource.status != "published":
                    raise ValueError("只能关联已发布资源")

            ref = self.db.query(CourseResourceRef).filter(
                CourseResourceRef.course_id == course_id,
                CourseResourceRef.resource_id == data.resource_id,
            ).first()

            if not ref:
                ref = CourseResourceRef(
                    course_id=course_id,
                    resource_id=data.resource_id,
                    library_item_id=None,
                    usage_type=data.usage_type,
                    sort_order=data.sort_order,
                )
                self.db.add(ref)
            else:
                ref.usage_type = data.usage_type
                ref.sort_order = data.sort_order

        self.db.commit()
        loaded_ref = self._get_course_resource_ref(course_id, ref.id)
        if not loaded_ref:
            raise ValueError("课程资源绑定结果不存在")
        response = self._course_resource_ref_to_response(loaded_ref)
        if not response:
            raise ValueError("课程资源绑定结果无效")
        return response

    def list_course_resources(self, course_id: int) -> List[CourseBoundResourceResponse]:
        refs = (
            self.db.query(CourseResourceRef)
            .options(
                joinedload(CourseResourceRef.resource).joinedload(Resource.uploader),
                joinedload(CourseResourceRef.resource).joinedload(Resource.owner_department),
                joinedload(CourseResourceRef.resource).joinedload(Resource.cover_media),
                joinedload(CourseResourceRef.resource)
                .selectinload(Resource.tag_relations)
                .joinedload(ResourceTagRelation.tag),
                joinedload(CourseResourceRef.resource)
                .selectinload(Resource.media_links)
                .joinedload(ResourceMediaLink.media_file),
                joinedload(CourseResourceRef.library_item).joinedload(LibraryItem.media_file),
                joinedload(CourseResourceRef.library_item).joinedload(LibraryItem.owner).selectinload(User.departments),
            )
            .filter(CourseResourceRef.course_id == course_id)
            .order_by(CourseResourceRef.sort_order.asc(), CourseResourceRef.id.asc())
            .all()
        )

        items: List[CourseBoundResourceResponse] = []
        for ref in refs:
            response = self._course_resource_ref_to_response(ref)
            if response:
                items.append(response)
        return items

    def remove_course_resource(self, course_id: int, resource_id: int) -> bool:
        ref = self._get_course_resource_ref(course_id, resource_id)
        if not ref:
            ref = self.db.query(CourseResourceRef).filter(
                CourseResourceRef.course_id == course_id,
                or_(
                    CourseResourceRef.resource_id == resource_id,
                    CourseResourceRef.library_item_id == resource_id,
                ),
            ).order_by(CourseResourceRef.id.desc()).first()
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
                selectinload(Course.chapters).joinedload(Chapter.file),
                selectinload(Course.chapters).joinedload(Chapter.library_item).joinedload(LibraryItem.media_file),
                selectinload(Course.chapters).joinedload(Chapter.resource)
                .selectinload(Resource.media_links)
                .joinedload(ResourceMediaLink.media_file),
                selectinload(Course.tag_relations).joinedload(CourseTagRelation.tag),
            )
            .filter(Course.id == course_id)
            .first()
        )

    def _get_scope_user(self, user_id: Optional[int]) -> Optional[User]:
        if not user_id:
            return None
        return self.db.query(User).options(
            joinedload(User.roles),
            joinedload(User.departments),
        ).filter(
            User.id == user_id,
            User.is_active == True,
        ).first()

    def _has_role(self, user: Optional[User], role_code: str) -> bool:
        if not user or not role_code:
            return False
        return any(
            getattr(role, "is_active", True) and str(role.code or "").strip() == role_code
            for role in (user.roles or [])
        )

    def _is_admin_user(self, user: Optional[User]) -> bool:
        return self._has_role(user, "admin")

    def _normalize_scope_target_ids(self, values: Any) -> List[int]:
        normalized: List[int] = []
        seen = set()
        for raw_item in values or []:
            try:
                item = int(raw_item)
            except (TypeError, ValueError):
                continue
            if item <= 0 or item in seen:
                continue
            seen.add(item)
            normalized.append(item)
        return normalized

    def _build_scope_summary(self, label: str, names: List[str]) -> str:
        cleaned_names = [str(name).strip() for name in names if str(name or "").strip()]
        if not cleaned_names:
            return label
        if len(cleaned_names) <= 3:
            return f"{label}：{'、'.join(cleaned_names)}"
        return f"{label}：{'、'.join(cleaned_names[:3])} 等{len(cleaned_names)}项"

    def _display_user_name(self, user: Optional[User]) -> str:
        if not user:
            return ""
        return str(user.nickname or user.username or user.id)

    def _prepare_course_scope(
        self,
        scope_type: Optional[str],
        scope_target_ids: Any,
    ) -> tuple[str, List[int], str]:
        resolved_scope_type = str(scope_type or ADMISSION_SCOPE_ALL).strip() or ADMISSION_SCOPE_ALL
        target_ids = self._normalize_scope_target_ids(scope_target_ids)

        if resolved_scope_type == ADMISSION_SCOPE_ALL:
            return ADMISSION_SCOPE_ALL, [], "全体用户"

        if not target_ids:
            raise ValueError("请至少选择一个可见范围目标")

        if resolved_scope_type == ADMISSION_SCOPE_USER:
            users = self.db.query(User).filter(
                User.id.in_(target_ids),
                User.is_active == True,
            ).all()
            user_map = {user.id: user for user in users}
            ordered_users = [user_map.get(item_id) for item_id in target_ids]
            if not all(ordered_users):
                raise ValueError("指定用户中包含无效用户")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定用户", [self._display_user_name(user) for user in ordered_users]),
            )

        if resolved_scope_type == ADMISSION_SCOPE_DEPARTMENT:
            departments = self.db.query(Department).filter(
                Department.id.in_(target_ids),
                Department.is_active == True,
            ).all()
            department_map = {department.id: department for department in departments}
            ordered_departments = [department_map.get(item_id) for item_id in target_ids]
            if not all(ordered_departments):
                raise ValueError("指定部门中包含无效部门")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定部门", [department.name for department in ordered_departments]),
            )

        if resolved_scope_type == ADMISSION_SCOPE_ROLE:
            roles = self.db.query(Role).filter(
                Role.id.in_(target_ids),
                Role.is_active == True,
            ).all()
            role_map = {role.id: role for role in roles}
            ordered_roles = [role_map.get(item_id) for item_id in target_ids]
            if not all(ordered_roles):
                raise ValueError("指定角色中包含无效角色")
            return (
                resolved_scope_type,
                target_ids,
                self._build_scope_summary("指定角色", [role.name for role in ordered_roles]),
            )

        raise ValueError("不支持的可见范围类型")

    def _can_manage_course(self, course: Optional[Course], user: Optional[User]) -> bool:
        if not course or not user or not user.is_active:
            return False
        if self._is_admin_user(user):
            return True
        return user.id in {course.created_by, course.instructor_id}

    def _can_view_course(
        self,
        course: Optional[Course],
        user: Optional[User],
        scope_context: Optional[DataScopeContext] = None,
    ) -> bool:
        if not course or not user or not user.is_active:
            return False
        if self._can_manage_course(course, user):
            return True

        # 角色数据范围过滤：按课程创建者的部门和警种判断
        if scope_context and not scope_context.is_admin:
            creator = self._get_scope_user(course.created_by) if course.created_by else None
            if creator:
                creator_dept_id = creator.departments[0].id if creator.departments else None
                creator_pt_id = creator.police_types[0].id if creator.police_types else None
                if not can_access_scoped_object(
                    scope_context,
                    department_id=creator_dept_id,
                    police_type_id=creator_pt_id,
                    owner_user_ids=[course.created_by, course.instructor_id],
                    dimension_mode="any",
                ):
                    return False

        scope_type = course.scope_type or ADMISSION_SCOPE_ALL
        target_ids = set(self._normalize_scope_target_ids(course.scope_target_ids))
        if scope_type == ADMISSION_SCOPE_ALL:
            return True
        if not target_ids:
            return False
        if scope_type == ADMISSION_SCOPE_USER:
            return user.id in target_ids
        if scope_type == ADMISSION_SCOPE_DEPARTMENT:
            return any(department.id in target_ids for department in (user.departments or []))
        if scope_type == ADMISSION_SCOPE_ROLE:
            return any(role.id in target_ids for role in (user.roles or []))
        return False

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

    def _upsert_course_chapters(
        self,
        course: Course,
        chapters_data: List[dict],
        actor_user_id: Optional[int] = None,
    ) -> None:
        existing_by_id = {chapter.id: chapter for chapter in (course.chapters or []) if chapter.id is not None}
        keep_ids = set()
        total_duration_seconds = 0

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
            next_resource_id, next_library_item_id, next_file_id, next_content_type, next_duration_seconds = self._resolve_chapter_binding(
                chapter=chapter,
                chapter_data=chapter_data,
                chapter_index=idx,
                actor_user_id=actor_user_id,
            )
            chapter.resource_id = next_resource_id
            chapter.library_item_id = next_library_item_id
            chapter.file_id = next_file_id
            chapter.duration = self._minutes_from_seconds(
                next_duration_seconds,
                fallback_minutes=chapter_data.get("duration", chapter.duration),
            )
            total_duration_seconds += next_duration_seconds

            if next_resource_id or next_library_item_id:
                chapter.video_url = None
                chapter.doc_url = None
            else:
                chapter.video_url = chapter_data.get("video_url", chapter.video_url)
                chapter.doc_url = chapter_data.get("doc_url", chapter.doc_url)
                if next_content_type == "video" and not chapter.video_url and next_file_id:
                    chapter.doc_url = None
                if next_content_type == "document" and not chapter.doc_url and next_file_id:
                    chapter.video_url = None

            if chapter.id is not None:
                keep_ids.add(chapter.id)

        for chapter_id, chapter in existing_by_id.items():
            if chapter_id in keep_ids:
                continue
            self.db.query(CourseProgress).filter(
                CourseProgress.course_id == course.id,
                CourseProgress.chapter_id == chapter_id,
            ).delete()
            self.db.delete(chapter)

        self.db.flush()
        course.duration = self._minutes_from_seconds(total_duration_seconds, fallback_minutes=course.duration)
        self._refresh_student_count(course.id)

    def _resolve_chapter_binding(
        self,
        chapter: Chapter,
        chapter_data: dict,
        chapter_index: int,
        actor_user_id: Optional[int] = None,
    ) -> tuple[Optional[int], Optional[int], Optional[int], Optional[str], int]:
        requested_resource_id = chapter_data.get("resource_id", chapter.resource_id)
        requested_library_item_id = chapter_data.get("library_item_id", getattr(chapter, "library_item_id", None))
        requested_file_id = chapter_data.get("file_id", chapter.file_id)

        if requested_library_item_id:
            library_item = (
                self.db.query(LibraryItem)
                .options(joinedload(LibraryItem.media_file))
                .filter(LibraryItem.id == requested_library_item_id)
                .first()
            )
            if not library_item:
                raise ValueError(f"第{chapter_index + 1}章所选资源不存在")

            existing_library_item_id = getattr(chapter, "library_item_id", None)
            existing_file_id = getattr(chapter, "file_id", None)
            binding_changed = existing_library_item_id != requested_library_item_id or existing_file_id != requested_file_id
            if actor_user_id and binding_changed and library_item.owner_user_id != actor_user_id:
                raise ValueError(f"第{chapter_index + 1}章只能引用当前用户自己的资源库资源")

            if library_item.content_type == "knowledge":
                return None, requested_library_item_id, None, "knowledge", self._minutes_to_seconds(
                    chapter_data.get("duration", chapter.duration),
                )

            media = getattr(library_item, "media_file", None)
            if not media:
                raise ValueError(f"第{chapter_index + 1}章所选资源没有可用文件")

            if requested_file_id is not None and int(requested_file_id) != int(media.id):
                raise ValueError(f"第{chapter_index + 1}章选择的文件不属于当前资源")

            content_type = library_item.content_type or self._guess_content_type(media.filename, media.mime_type)
            duration_seconds = self._resolve_media_duration_seconds(
                media,
                fallback_minutes=chapter_data.get("duration", chapter.duration),
            )
            return None, requested_library_item_id, media.id, content_type, duration_seconds

        if requested_resource_id:
            resource = (
                self.db.query(Resource)
                .options(joinedload(Resource.media_links).joinedload(ResourceMediaLink.media_file))
                .filter(Resource.id == requested_resource_id)
                .first()
            )
            if not resource:
                raise ValueError(f"第{chapter_index + 1}章所选资源不存在")

            existing_resource_id = getattr(chapter, "resource_id", None)
            existing_file_id = getattr(chapter, "file_id", None)
            binding_changed = existing_resource_id != requested_resource_id or existing_file_id != requested_file_id
            if actor_user_id and binding_changed:
                if resource.uploader_id != actor_user_id:
                    raise ValueError(f"第{chapter_index + 1}章只能引用当前用户自己上传的已发布资源")
                if resource.status != "published":
                    raise ValueError(f"第{chapter_index + 1}章只能引用已发布资源")

            ordered_links = sorted((resource.media_links or []), key=lambda item: (item.sort_order, item.id))
            if not ordered_links:
                raise ValueError(f"第{chapter_index + 1}章所选资源没有可用文件")

            media_by_id = {
                int(link.media_file_id): link
                for link in ordered_links
                if link.media_file_id is not None
            }
            selected_link = None
            if requested_file_id is not None:
                selected_link = media_by_id.get(int(requested_file_id))
                if not selected_link:
                    raise ValueError(f"第{chapter_index + 1}章选择的文件不属于当前资源")

            if not selected_link and existing_resource_id == requested_resource_id and existing_file_id is not None:
                selected_link = media_by_id.get(int(existing_file_id))

            if not selected_link:
                selected_link = next((link for link in ordered_links if link.media_role == "main"), None) or ordered_links[0]

            media = selected_link.media_file
            content_type = self._guess_content_type(
                getattr(media, "filename", None),
                getattr(media, "mime_type", None),
            ) or self._normalize_course_resource_content_type(resource.content_type)
            duration_seconds = self._resolve_media_duration_seconds(
                media,
                fallback_minutes=chapter_data.get("duration", chapter.duration),
            )
            return requested_resource_id, None, selected_link.media_file_id, content_type, duration_seconds

        if chapter.id and chapter.file_id:
            content_type = self._guess_content_type(chapter.video_url) or self._guess_content_type(chapter.doc_url)
            if not content_type and getattr(chapter, "file", None):
                content_type = self._guess_content_type(chapter.file.filename, chapter.file.mime_type)
            duration_seconds = self._resolve_media_duration_seconds(
                getattr(chapter, "file", None),
                fallback_minutes=chapter_data.get("duration", chapter.duration),
            )
            return None, None, chapter.file_id, content_type, duration_seconds

        raise ValueError(f"第{chapter_index + 1}章请从资源库选择当前用户自己的资源")

    def _normalize_duration_seconds(self, value: Any) -> int:
        try:
            normalized = int(value or 0)
        except (TypeError, ValueError):
            return 0
        return max(normalized, 0)

    def _minutes_to_seconds(self, value: Any) -> int:
        try:
            minutes = int(value or 0)
        except (TypeError, ValueError):
            return 0
        return max(minutes, 0) * 60

    def _minutes_from_seconds(self, duration_seconds: Any, fallback_minutes: Any = 0) -> int:
        normalized_seconds = self._normalize_duration_seconds(duration_seconds)
        if normalized_seconds > 0:
            return max(1, (normalized_seconds + 59) // 60)
        try:
            fallback = int(fallback_minutes or 0)
        except (TypeError, ValueError):
            return 0
        return max(fallback, 0)

    def _resolve_media_duration_seconds(
        self,
        media: Optional[MediaFile],
        fallback_minutes: Any = 0,
    ) -> int:
        if media:
            resolved = self._normalize_duration_seconds(getattr(media, "duration_seconds", 0))
            if resolved > 0:
                return resolved
        return self._minutes_to_seconds(fallback_minutes)

    def _resolve_course_duration_seconds(self, course: Optional[Course]) -> int:
        if not course:
            return 0
        total_duration_seconds = sum(
            self._resolve_chapter_duration_seconds(chapter)
            for chapter in (course.chapters or [])
        )
        if total_duration_seconds > 0:
            return total_duration_seconds
        return self._minutes_to_seconds(course.duration)

    def _resolve_chapter_duration_seconds(self, chapter: Optional[Chapter]) -> int:
        if not chapter:
            return 0
        return self._resolve_chapter_media_context(chapter)["duration_seconds"]

    def _resolve_chapter_media_context(self, chapter: Chapter) -> dict[str, Any]:
        file_url = None
        content_type = None
        resource_title = None
        resource_file_name = None
        resource_file_label = None
        knowledge_content_html = None
        duration_seconds = self._minutes_to_seconds(chapter.duration)

        if getattr(chapter, "library_item_id", None):
            library_item = getattr(chapter, "library_item", None)
            if library_item:
                resource_title = library_item.title
                content_type = library_item.content_type
                knowledge_content_html = library_item.knowledge_content_html
                media = getattr(library_item, "media_file", None)
                if media:
                    file_url = self._resolve_file_url(media.id, media.storage_path)
                    content_type = content_type or self._guess_content_type(media.filename, media.mime_type)
                    resource_file_name = media.filename
                    resource_file_label = "原始文件"
                    duration_seconds = self._resolve_media_duration_seconds(media, fallback_minutes=chapter.duration)

        if getattr(chapter, "resource_id", None):
            resource = getattr(chapter, "resource", None)
            if resource and resource.status == "published":
                links = sorted((resource.media_links or []), key=lambda item: (item.sort_order, item.id))
                media_by_id = {
                    int(link.media_file_id): link
                    for link in links
                    if link.media_file_id is not None
                }
                selected_link = media_by_id.get(int(chapter.file_id)) if chapter.file_id is not None else None
                if not selected_link:
                    selected_link = next((item for item in links if item.media_role == "main"), None) or (links[0] if links else None)
                media = selected_link.media_file if selected_link else None
                if media:
                    file_url = self._resolve_file_url(media.id, media.storage_path)
                    content_type = self._guess_content_type(media.filename, media.mime_type) or self._normalize_course_resource_content_type(resource.content_type)
                    resource_title = resource.title
                    resource_file_name = media.filename
                    resource_file_label = self._build_resource_file_label(links, selected_link)
                    duration_seconds = self._resolve_media_duration_seconds(media, fallback_minutes=chapter.duration)

        if not file_url and chapter.file_id:
            media = getattr(chapter, "file", None)
            if not media:
                media = self.db.query(MediaFile).filter(MediaFile.id == chapter.file_id).first()
            if media:
                file_url = self._resolve_file_url(media.id, media.storage_path)
                content_type = self._guess_content_type(media.filename, media.mime_type)
                duration_seconds = self._resolve_media_duration_seconds(media, fallback_minutes=chapter.duration)
            else:
                file_url = f"{settings.API_V1_STR}/media/files/{chapter.file_id}"

        if not content_type:
            content_type = (
                self._guess_content_type(chapter.video_url)
                or self._guess_content_type(chapter.doc_url)
                or "video"
            )

        return {
            "file_url": file_url,
            "content_type": content_type,
            "resource_title": resource_title,
            "resource_file_name": resource_file_name,
            "resource_file_label": resource_file_label,
            "knowledge_content_html": knowledge_content_html,
            "duration_seconds": duration_seconds,
        }

    def _resolve_learning_status(
        self,
        progress_percent: int,
        chapter_count: int,
        completed_chapter_count: int = 0,
        has_activity: bool = False,
    ) -> str:
        normalized_progress = min(max(int(progress_percent or 0), 0), 100)
        normalized_chapter_count = max(int(chapter_count or 0), 0)
        normalized_completed_count = max(int(completed_chapter_count or 0), 0)
        if normalized_chapter_count > 0 and normalized_completed_count >= normalized_chapter_count:
            return "completed"
        if normalized_progress >= 100:
            return "completed"
        if normalized_progress > 0 or has_activity:
            return "in_progress"
        return "not_started"

    def _build_course_sort_key(self, item: CourseListResponse, sort: Optional[str]) -> tuple[Any, ...]:
        resolved_sort = str(sort or "latest").strip() or "latest"
        created_rank = -self._to_timestamp(item.created_at)
        last_studied_rank = -self._to_timestamp(item.last_studied_at)
        rating_rank = -float(item.rating or 0)
        student_rank = -int(item.student_count or 0)
        progress_rank = -int(item.progress_percent or 0)
        duration_rank = self._normalize_duration_seconds(item.duration_seconds) or self._minutes_to_seconds(item.duration)
        required_rank = 0 if item.is_required else 1
        learning_rank = self._learning_status_sort_rank(item.learning_status)

        if resolved_sort == "rating":
            return (rating_rank, student_rank, created_rank, -item.id)
        if resolved_sort == "students":
            return (student_rank, rating_rank, created_rank, -item.id)
        if resolved_sort == "required_first":
            return (required_rank, learning_rank, last_studied_rank, created_rank, -item.id)
        if resolved_sort == "learning_priority":
            return (learning_rank, required_rank, progress_rank, last_studied_rank, created_rank, -item.id)
        if resolved_sort == "duration_asc":
            return (duration_rank or 10 ** 12, required_rank, created_rank, -item.id)
        return (created_rank, required_rank, -item.id)

    def _learning_status_sort_rank(self, learning_status: Optional[str]) -> int:
        status = str(learning_status or "").strip()
        if status == "in_progress":
            return 0
        if status == "not_started":
            return 1
        if status == "completed":
            return 2
        return 3

    def _to_timestamp(self, value: Optional[datetime]) -> float:
        if not value:
            return 0.0
        return value.timestamp()

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
        if "audio" in mime or source.endswith((".mp3", ".wav", ".m4a")):
            return "audio"
        if "image" in mime or source.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            return "image"
        if "html" in mime or "pdf" in mime or any(source.endswith(ext) for ext in (".pdf", ".ppt", ".pptx", ".doc", ".docx", ".html", ".htm")):
            return "document"
        return None

    def _normalize_course_resource_content_type(self, content_type: Optional[str]) -> Optional[str]:
        if content_type == "image_text":
            return "image"
        return content_type

    def _normalize_course_file_type(self, file_type: Optional[str]) -> Optional[str]:
        normalized = (file_type or "").strip().lower()
        if normalized == "image_text":
            normalized = "image"
        if normalized in {"video", "audio", "image", "document", "knowledge", "mixed", "pending"}:
            return normalized
        return None

    def _normalize_course_difficulty(self, difficulty: Optional[Any], default: int = 1) -> int:
        try:
            normalized = int(difficulty if difficulty is not None else default)
        except (TypeError, ValueError):
            normalized = default
        return min(max(normalized, 1), 5)

    def _infer_course_file_type_from_chapters(self, chapters: List[Chapter]) -> str:
        content_types = {
            self._normalize_course_resource_content_type(self._resolve_chapter_media_context(chapter)["content_type"])
            for chapter in (chapters or [])
        }
        normalized_types = {
            item for item in content_types
            if item in {"video", "audio", "image", "document", "knowledge"}
        }
        if not normalized_types:
            return "document"
        if len(normalized_types) > 1:
            return "mixed"
        return next(iter(normalized_types))

    def _sync_course_shell_state(
        self,
        course: Course,
        preferred_file_type: Optional[str] = None,
        infer_from_chapters: bool = False,
    ) -> None:
        chapters = sorted(course.chapters or [], key=lambda item: (item.sort_order, item.id or 0))
        if not chapters:
            course.duration = 0
            course.file_type = "pending"
            return

        if infer_from_chapters:
            course.file_type = self._infer_course_file_type_from_chapters(chapters)
            return

        normalized_preferred = self._normalize_course_file_type(preferred_file_type)
        if normalized_preferred and normalized_preferred != "pending":
            course.file_type = normalized_preferred
            return

        normalized_current = self._normalize_course_file_type(course.file_type)
        if not normalized_current or normalized_current == "pending":
            course.file_type = self._infer_course_file_type_from_chapters(chapters)

    def _resolve_course_file_type_for_response(self, course: Course, chapters: Optional[List[Chapter]] = None) -> str:
        normalized_current = self._normalize_course_file_type(course.file_type)
        ordered_chapters = list(chapters if chapters is not None else (course.chapters or []))
        if not ordered_chapters:
            return "pending"
        if normalized_current and normalized_current != "pending":
            return normalized_current
        return self._infer_course_file_type_from_chapters(ordered_chapters)

    def _build_resource_file_label(
        self,
        media_links: List[ResourceMediaLink],
        current_link: Optional[ResourceMediaLink],
    ) -> Optional[str]:
        if not current_link:
            return None
        for index, item in enumerate(media_links or [], start=1):
            if item.id == current_link.id:
                return f"文件{index}"
        return "文件"

    def _resolve_training_relation_roles(
        self,
        training: Optional[Training],
        training_course: Optional[TrainingCourse],
        user_id: int,
        is_admin: bool = False,
    ) -> List[str]:
        roles: List[str] = []
        if is_admin:
            roles.append("管理员")
        if training and training.instructor_id == user_id:
            roles.append("班主任")
        if training_course and training_course.primary_instructor_id == user_id:
            roles.append("主讲教官")
        if training_course and user_id in (training_course.assistant_instructor_ids or []):
            roles.append("助教")
        return roles

    def _get_course_resource_ref(self, course_id: int, ref_id: int) -> Optional[CourseResourceRef]:
        return self.db.query(CourseResourceRef).options(
            joinedload(CourseResourceRef.resource).joinedload(Resource.uploader),
            joinedload(CourseResourceRef.resource).joinedload(Resource.owner_department),
            joinedload(CourseResourceRef.resource).joinedload(Resource.cover_media),
            joinedload(CourseResourceRef.resource)
            .selectinload(Resource.tag_relations)
            .joinedload(ResourceTagRelation.tag),
            joinedload(CourseResourceRef.resource)
            .selectinload(Resource.media_links)
            .joinedload(ResourceMediaLink.media_file),
            joinedload(CourseResourceRef.library_item).joinedload(LibraryItem.media_file),
            joinedload(CourseResourceRef.library_item).joinedload(LibraryItem.owner).selectinload(User.departments),
        ).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.id == ref_id,
        ).first()

    def _course_resource_ref_to_response(self, ref: CourseResourceRef) -> Optional[CourseBoundResourceResponse]:
        if ref.library_item:
            item = ref.library_item
            media = item.media_file
            owner = item.owner
            owner_department = (owner.departments or [None])[0] if owner else None
            return CourseBoundResourceResponse(
                id=ref.id,
                ref_id=ref.id,
                binding_type="library_item",
                resource_id=None,
                library_item_id=item.id,
                title=item.title,
                summary=None,
                content_type=item.content_type,
                source_type=item.source_kind,
                source_label="个人资源库",
                status="public" if item.is_public else "private",
                status_label="公共资源" if item.is_public else "私人资源",
                visibility_type="public" if item.is_public else "private",
                uploader_id=item.owner_user_id,
                uploader_name=(owner.nickname or owner.username) if owner else None,
                owner_department_id=owner_department.id if owner_department else None,
                owner_department_name=owner_department.name if owner_department else None,
                cover_media_file_id=None,
                cover_url=None,
                tags=[],
                file_id=item.media_file_id,
                file_name=media.filename if media else None,
                file_url=self._resolve_file_url(media.id, media.storage_path) if media else None,
                mime_type=media.mime_type if media else None,
                duration_seconds=int(media.duration_seconds or 0) if media else 0,
                knowledge_content_html=item.knowledge_content_html,
                is_public=bool(item.is_public),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )

        resource = ref.resource
        if not resource:
            return None

        cover_media = resource.cover_media
        media_links = sorted(
            resource.media_links or [],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        primary_media = next((link.media_file for link in media_links if link.media_file), None)
        tags = [rel.tag.name for rel in (resource.tag_relations or []) if rel.tag]
        return CourseBoundResourceResponse(
            id=ref.id,
            ref_id=ref.id,
            binding_type="resource",
            resource_id=resource.id,
            library_item_id=None,
            title=resource.title,
            summary=resource.summary,
            content_type=self._normalize_course_resource_content_type(resource.content_type) or resource.content_type,
            source_type=resource.source_type,
            source_label="公共资源",
            status=resource.status,
            status_label=self._get_course_resource_status_label(resource.status),
            visibility_type=resource.visibility_type,
            uploader_id=resource.uploader_id,
            uploader_name=resource.uploader.nickname if resource.uploader else None,
            owner_department_id=resource.owner_department_id,
            owner_department_name=resource.owner_department.name if resource.owner_department else None,
            cover_media_file_id=resource.cover_media_file_id,
            cover_url=self._resolve_file_url(cover_media.id, cover_media.storage_path) if cover_media else None,
            tags=tags,
            file_id=primary_media.id if primary_media else None,
            file_name=primary_media.filename if primary_media else None,
            file_url=self._resolve_file_url(primary_media.id, primary_media.storage_path) if primary_media else None,
            mime_type=primary_media.mime_type if primary_media else None,
            duration_seconds=int(primary_media.duration_seconds or 0) if primary_media else 0,
            knowledge_content_html=None,
            is_public=None,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )

    def _get_course_resource_status_label(self, status: Optional[str]) -> Optional[str]:
        status_map = {
            "draft": "草稿",
            "pending_review": "待审核",
            "reviewing": "审核中",
            "published": "已发布",
            "rejected": "已驳回",
            "offline": "已下线",
        }
        if not status:
            return None
        return status_map.get(status, status)

    def _chapter_to_response(
        self,
        chapter: Chapter,
        progress_summary=None,
    ) -> ChapterResponse:
        """转换章节为响应，填充 file_url、类型和用户进度"""
        media_context = self._resolve_chapter_media_context(chapter)
        progress_record = None
        if progress_summary:
            progress_record = progress_summary.chapter_records.get(chapter.id)

        return ChapterResponse(
            id=chapter.id,
            course_id=chapter.course_id,
            title=chapter.title,
            sort_order=chapter.sort_order,
            duration=self._minutes_from_seconds(media_context["duration_seconds"], fallback_minutes=chapter.duration),
            duration_seconds=media_context["duration_seconds"],
            video_url=chapter.video_url,
            doc_url=chapter.doc_url,
            file_id=chapter.file_id,
            resource_id=getattr(chapter, "resource_id", None),
            library_item_id=getattr(chapter, "library_item_id", None),
            resource_title=media_context["resource_title"],
            resource_file_name=media_context["resource_file_name"],
            resource_file_label=media_context["resource_file_label"],
            file_url=media_context["file_url"],
            content_type=media_context["content_type"],
            knowledge_content_html=media_context["knowledge_content_html"],
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
        resolved_duration_seconds = self._resolve_course_duration_seconds(course)
        resolved_chapter_count = progress_summary.chapter_count if progress_summary else len(sorted_chapters)
        resolved_completed_chapter_count = progress_summary.completed_chapter_count if progress_summary else 0
        resolved_progress_percent = progress_summary.progress_percent if progress_summary else 0
        current_user = self._get_scope_user(user_id) if user_id else None
        has_learning_activity = bool(
            progress_summary and (
                progress_summary.last_studied_at
                or progress_summary.last_playback_seconds > 0
                or any(
                    (record.progress or 0) > 0 or (record.playback_seconds or 0) > 0
                    for record in progress_summary.chapter_records.values()
                )
            )
        )

        return CourseResponse(
            id=course.id,
            title=course.title,
            category=course.category,
            file_type=self._resolve_course_file_type_for_response(course, sorted_chapters),
            description=course.description,
            created_by=course.created_by,
            created_by_name=course.creator.nickname if course.creator else None,
            instructor_id=course.instructor_id,
            instructor_name=course.instructor.nickname if course.instructor else None,
            duration=self._minutes_from_seconds(resolved_duration_seconds, fallback_minutes=course.duration),
            duration_seconds=resolved_duration_seconds,
            student_count=course.student_count,
            rating=course.rating,
            difficulty=course.difficulty,
            is_required=course.is_required,
            cover_color=course.cover_color,
            scope=course.scope,
            scope_type=course.scope_type or ADMISSION_SCOPE_ALL,
            scope_target_ids=self._normalize_scope_target_ids(course.scope_target_ids),
            tags=self._course_tags(course),
            progress_percent=resolved_progress_percent,
            learning_status=self._resolve_learning_status(
                resolved_progress_percent,
                resolved_chapter_count,
                resolved_completed_chapter_count,
                has_learning_activity,
            ),
            chapter_count=resolved_chapter_count,
            completed_chapter_count=resolved_completed_chapter_count,
            last_studied_at=progress_summary.last_studied_at if progress_summary else None,
            last_studied_chapter_id=progress_summary.last_studied_chapter_id if progress_summary else None,
            last_studied_chapter_title=progress_summary.last_studied_chapter_title if progress_summary else None,
            last_playback_seconds=progress_summary.last_playback_seconds if progress_summary else 0,
            can_view_learning_status=(
                self._can_view_learning_status(course, user_id, user_permissions)
                if user_id
                else False
            ),
            can_manage_course=self._can_manage_course(course, current_user),
            chapters=chapters,
            note=note,
            qa_list=qa_list,
            resources=resources,
            related_trainings=(
                self.list_related_trainings(course.id, user_id, current_user=current_user)
                if user_id and current_user
                else []
            ),
            created_at=course.created_at,
            updated_at=course.updated_at,
        )
