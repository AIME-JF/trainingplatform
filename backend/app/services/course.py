"""
课程管理服务
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, cast, String

from app.models.course import Course, Chapter, CourseNote, CourseProgress, CourseQA
from app.models.user import User
from app.models.media import MediaFile
from app.models.resource import Resource, ResourceMediaLink, CourseResourceRef, ResourceTagRelation
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    ChapterResponse, CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse,
    CourseQACreate, CourseQAResponse
)
from app.schemas.resource import CourseResourceBindRequest, ResourceListItemResponse
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
                    doc_url=ch.doc_url, file_id=ch.file_id,
                    resource_id=getattr(ch, 'resource_id', None)
                )
                self.db.add(chapter)

        self.db.commit()
        self.db.refresh(course)
        logger.info(f"创建课程: {course.title}")
        return self._to_response(course)

    def get_course_by_id(self, course_id: int, user_id: Optional[int] = None) -> Optional[CourseResponse]:
        """获取课程详情（含当前用户的章节进度）"""
        course = self.db.query(Course).options(
            joinedload(Course.instructor),
            joinedload(Course.chapters)
        ).filter(Course.id == course_id).first()

        if not course:
            return None
        return self._to_response(course, user_id=user_id)

    def update_course(self, course_id: int, data: CourseUpdate) -> Optional[CourseResponse]:
        """更新课程"""
        course = self.db.query(Course).options(joinedload(Course.chapters)).filter(Course.id == course_id).first()
        if not course:
            return None

        update_data = data.model_dump(exclude_none=True)  # 使用 exclude_none 而非 exclude_unset，这样 tags=[] 空数组也会被正确保存
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
                    file_id=ch.get('file_id'),
                    resource_id=ch.get('resource_id')
                )
                self.db.add(chapter)

        self.db.commit()
        course = self.db.query(Course).options(
            joinedload(Course.instructor),
            joinedload(Course.chapters)
        ).filter(Course.id == course_id).first()
        logger.info(f"更新课程: {course.title}")
        return self._to_response(course)

    def delete_course(self, course_id: int) -> bool:
        """删除课程及其关联的章节、笔记、进度记录"""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return False

        # 删除关联的学习进度
        self.db.query(CourseProgress).filter(CourseProgress.course_id == course_id).delete()
        # 删除关联的课程笔记
        self.db.query(CourseNote).filter(CourseNote.course_id == course_id).delete()
        # 删除关联的章节
        self.db.query(Chapter).filter(Chapter.course_id == course_id).delete()
        # 删除课程本体
        self.db.delete(course)
        self.db.commit()
        logger.info(f"课程已删除: id={course_id}, title={course.title}")
        return True

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

        # 实时更新 student_count：统计此课程有学习记录的不重复用户数
        try:
            from sqlalchemy import func as sa_func
            real_count = self.db.query(sa_func.count(sa_func.distinct(CourseProgress.user_id))).filter(
                CourseProgress.course_id == course_id
            ).scalar() or 0
            self.db.query(Course).filter(Course.id == course_id).update({'student_count': real_count})
            self.db.commit()
        except Exception as e:
            logger.warning(f"更新 student_count 失败: {e}")

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

    def add_course_resource(self, course_id: int, data: CourseResourceBindRequest) -> ResourceListItemResponse:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError('课程不存在')

        resource = self.db.query(Resource).options(
            joinedload(Resource.uploader),
            joinedload(Resource.owner_department),
            joinedload(Resource.cover_media),
            joinedload(Resource.tag_relations).joinedload(ResourceTagRelation.tag)
        ).filter(Resource.id == data.resource_id).first()
        if not resource:
            raise ValueError('资源不存在')

        ref = self.db.query(CourseResourceRef).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.resource_id == data.resource_id
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
        refs = self.db.query(CourseResourceRef).options(
            joinedload(CourseResourceRef.resource).joinedload(Resource.uploader),
            joinedload(CourseResourceRef.resource).joinedload(Resource.owner_department),
            joinedload(CourseResourceRef.resource).joinedload(Resource.cover_media),
            joinedload(CourseResourceRef.resource).selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(CourseResourceRef.course_id == course_id).order_by(CourseResourceRef.sort_order.asc(), CourseResourceRef.id.asc()).all()

        items = []
        for ref in refs:
            r = ref.resource
            if not r:
                continue
            tags = [rel.tag.name for rel in (r.tag_relations or []) if rel.tag]
            items.append(ResourceListItemResponse(
                id=r.id,
                title=r.title,
                summary=r.summary,
                content_type=r.content_type,
                source_type=r.source_type,
                status=r.status,
                visibility_type=r.visibility_type,
                uploader_id=r.uploader_id,
                uploader_name=r.uploader.nickname if r.uploader else None,
                owner_department_id=r.owner_department_id,
                owner_department_name=r.owner_department.name if r.owner_department else None,
                cover_media_file_id=r.cover_media_file_id,
                cover_url=None,
                tags=tags,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ))
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

    def _chapter_to_response(self, ch: Chapter, user_progress: dict = None) -> ChapterResponse:
        """转换章节为响应，填充 file_url 和用户进度"""
        file_url = None
        if getattr(ch, 'resource_id', None):
            resource = self.db.query(Resource).options(
                joinedload(Resource.media_links).joinedload(ResourceMediaLink.media_file)
            ).filter(Resource.id == ch.resource_id).first()
            if resource and resource.status == 'published':
                links = sorted((resource.media_links or []), key=lambda x: x.sort_order)
                main_link = next((l for l in links if l.media_role == 'main'), None) or (links[0] if links else None)
                media = main_link.media_file if main_link else None
                if media and media.storage_path:
                    base = (settings.MINIO_PUBLIC_URL or "").rstrip("/")
                    bucket = (settings.MINIO_BUCKET or "").strip("/")
                    path = media.storage_path.lstrip("/")
                    if base and bucket and path:
                        file_url = f"{base}/{bucket}/{path}"
                    else:
                        file_url = f"{settings.API_V1_STR}/media/files/{media.id}"

        if not file_url and ch.file_id:
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
        progress = (user_progress or {}).get(ch.id, 0)
        resp = ChapterResponse(
            id=ch.id, course_id=ch.course_id, title=ch.title,
            sort_order=ch.sort_order, duration=ch.duration,
            video_url=ch.video_url, doc_url=ch.doc_url,
            file_id=ch.file_id, resource_id=getattr(ch, 'resource_id', None), file_url=file_url,
            progress=progress,
        )
        return resp

    def _to_response(self, course: Course, user_id: Optional[int] = None) -> CourseResponse:
        """转换为响应，user_id 用于注入章节进度"""
        # 预查询该用户对这门课的所有章节进度
        user_progress = {}
        if user_id:
            records = self.db.query(CourseProgress).filter(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course.id
            ).all()
            user_progress = {r.chapter_id: r.progress for r in records}

        chapters = []
        if hasattr(course, 'chapters') and course.chapters:
            chapters = [self._chapter_to_response(ch, user_progress) for ch in
                        sorted(course.chapters, key=lambda x: x.sort_order)]
        note = self.get_course_note(course.id, user_id) if user_id else None
        qa_list = self.get_course_qa(course.id)
        resources = self.list_course_resources(course.id)

        return CourseResponse(
            id=course.id, title=course.title, category=course.category,
            file_type=course.file_type, description=course.description,
            instructor_id=course.instructor_id,
            instructor_name=course.instructor.nickname if course.instructor else None,
            duration=course.duration, student_count=course.student_count,
            rating=course.rating, difficulty=course.difficulty,
            is_required=course.is_required, cover_color=course.cover_color,
            tags=course.tags, chapters=chapters,
            note=note, qa_list=qa_list, resources=resources,
            created_at=course.created_at, updated_at=course.updated_at
        )
    def get_course_qa(self, course_id: int) -> List[CourseQAResponse]:
        """获取课程答疑列表"""
        qa_list = self.db.query(CourseQA).options(joinedload(CourseQA.user)).filter(
            CourseQA.course_id == course_id
        ).order_by(CourseQA.created_at.desc()).all()
        
        results = []
        for qa in qa_list:
            results.append(CourseQAResponse(
                id=qa.id,
                user_id=qa.user_id,
                user_name=qa.user.nickname if qa.user else "未知用户",
                course_id=qa.course_id,
                question=qa.question,
                answer=qa.answer,
                created_at=qa.created_at,
                updated_at=qa.updated_at
            ))
        return results

    def create_course_qa(self, course_id: int, user_id: int, data: CourseQACreate) -> CourseQAResponse:
        """创建课程提问"""
        qa = CourseQA(
            user_id=user_id,
            course_id=course_id,
            question=data.question
        )
        self.db.add(qa)
        self.db.commit()
        self.db.refresh(qa)
        
        # 关联查询用户信息
        user = self.db.query(User).filter(User.id == user_id).first()
        
        return CourseQAResponse(
            id=qa.id,
            user_id=qa.user_id,
            user_name=user.nickname if user else "我",
            course_id=qa.course_id,
            question=qa.question,
            answer=qa.answer,
            created_at=qa.created_at,
            updated_at=qa.updated_at
        )
