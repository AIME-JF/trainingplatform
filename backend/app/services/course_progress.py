"""
课程学习进度聚合服务
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import Chapter, Course, CourseProgress, User


@dataclass
class CourseProgressSummary:
    progress_percent: int = 0
    chapter_count: int = 0
    completed_chapter_count: int = 0
    last_studied_at: Optional[datetime] = None
    last_studied_chapter_id: Optional[int] = None
    last_studied_chapter_title: Optional[str] = None
    last_playback_seconds: int = 0
    chapter_records: Dict[int, CourseProgress] = field(default_factory=dict)


class CourseProgressService:
    """统一课程学习进度口径。"""

    def __init__(self, db: Session):
        self.db = db

    def build_summary(
        self,
        chapters: Iterable[Chapter],
        progress_records: Iterable[CourseProgress],
    ) -> CourseProgressSummary:
        ordered_chapters = list(chapters or [])
        record_list = list(progress_records or [])
        record_map = {
            record.chapter_id: record
            for record in record_list
            if record.chapter_id is not None
        }

        chapter_count = len(ordered_chapters)
        completed_chapter_count = sum(
            1
            for chapter in ordered_chapters
            if (record_map.get(chapter.id).progress if record_map.get(chapter.id) else 0) >= 100
        )

        total_weight = sum(
            max(int(chapter.duration or 0), 0)
            for chapter in ordered_chapters
            if int(chapter.duration or 0) > 0
        )
        if total_weight > 0:
            weighted_progress = round(
                sum(
                    max(int(chapter.duration or 0), 0)
                    * min(max(record_map.get(chapter.id).progress if record_map.get(chapter.id) else 0, 0), 100)
                    for chapter in ordered_chapters
                ) / total_weight
            )
        elif chapter_count > 0:
            weighted_progress = round(
                sum(
                    min(max(record_map.get(chapter.id).progress if record_map.get(chapter.id) else 0, 0), 100)
                    for chapter in ordered_chapters
                ) / chapter_count
            )
        else:
            weighted_progress = 0

        latest_record = max(
            record_list,
            key=lambda item: item.last_studied_at or datetime.min,
            default=None,
        )
        latest_chapter = next(
            (chapter for chapter in ordered_chapters if chapter.id == getattr(latest_record, "chapter_id", None)),
            None,
        )

        return CourseProgressSummary(
            progress_percent=min(max(weighted_progress, 0), 100),
            chapter_count=chapter_count,
            completed_chapter_count=completed_chapter_count,
            last_studied_at=latest_record.last_studied_at if latest_record else None,
            last_studied_chapter_id=latest_chapter.id if latest_chapter else None,
            last_studied_chapter_title=latest_chapter.title if latest_chapter else None,
            last_playback_seconds=max(int(getattr(latest_record, "playback_seconds", 0) or 0), 0),
            chapter_records=record_map,
        )

    def get_user_course_summaries(
        self,
        user_id: int,
        courses: Iterable[Course],
    ) -> Dict[int, CourseProgressSummary]:
        course_list = list(courses or [])
        course_ids = [course.id for course in course_list if getattr(course, "id", None) is not None]
        if not course_ids:
            return {}

        records = (
            self.db.query(CourseProgress)
            .filter(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id.in_(course_ids),
            )
            .all()
        )
        records_by_course: Dict[int, List[CourseProgress]] = {}
        for record in records:
            records_by_course.setdefault(record.course_id, []).append(record)

        summaries: Dict[int, CourseProgressSummary] = {}
        for course in course_list:
            course_chapters = sorted(course.chapters or [], key=lambda item: item.sort_order)
            summaries[course.id] = self.build_summary(
                course_chapters,
                records_by_course.get(course.id, []),
            )
        return summaries

    def get_course_learning_status(self, course: Course) -> List[dict]:
        course_chapters = sorted(course.chapters or [], key=lambda item: item.sort_order)
        if not course_chapters:
            return []

        records = (
            self.db.query(CourseProgress)
            .filter(CourseProgress.course_id == course.id)
            .all()
        )
        if not records:
            return []

        records_by_user: Dict[int, List[CourseProgress]] = {}
        for record in records:
            records_by_user.setdefault(record.user_id, []).append(record)

        users = (
            self.db.query(User)
            .options(selectinload(User.departments))
            .filter(User.id.in_(list(records_by_user.keys())), User.is_active == True)
            .all()
        )
        users_by_id = {user.id: user for user in users}

        items: List[dict] = []
        for user_id, user_records in records_by_user.items():
            user = users_by_id.get(user_id)
            if not user:
                continue
            summary = self.build_summary(course_chapters, user_records)
            items.append({
                "user_id": user.id,
                "username": user.username,
                "user_name": user.nickname or user.username,
                "police_id": user.police_id,
                "department_name": user.departments[0].name if user.departments else None,
                "progress_percent": summary.progress_percent,
                "chapter_count": summary.chapter_count,
                "completed_chapter_count": summary.completed_chapter_count,
                "last_studied_at": summary.last_studied_at,
                "last_studied_chapter_id": summary.last_studied_chapter_id,
                "last_studied_chapter_title": summary.last_studied_chapter_title,
                "last_playback_seconds": summary.last_playback_seconds,
            })

        items.sort(
            key=lambda item: (
                item["last_studied_at"] or datetime.min,
                item["progress_percent"],
            ),
            reverse=True,
        )
        return items
