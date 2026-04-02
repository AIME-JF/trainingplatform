"""
通知服务
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Notice, NoticeRead
from app.schemas import PaginatedResponse
from app.schemas.notice import NoticeResponse, NoticeUnreadCountResponse


class NoticeService:
    """通知相关服务"""

    def __init__(self, db: Session):
        self.db = db

    def to_response(self, notice: Notice, user_id: Optional[int] = None) -> NoticeResponse:
        is_read = False
        if user_id and hasattr(notice, "reads"):
            is_read = any(read.user_id == user_id for read in (notice.reads or []))

        return NoticeResponse(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            type=notice.type,
            training_id=notice.training_id,
            author_id=notice.author_id,
            author_name=notice.author.nickname if notice.author else None,
            target_user_id=notice.target_user_id,
            reminder_type=notice.reminder_type,
            is_read=is_read,
            created_at=notice.created_at,
            updated_at=notice.updated_at,
        )

    def get_my_notifications(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        tab: Optional[str] = None,
    ) -> PaginatedResponse[NoticeResponse]:
        query = self._build_my_notice_query(user_id, tab)
        total = query.count()
        skip = (page - 1) * size
        records = query.order_by(Notice.created_at.desc()).offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page,
            size=size,
            total=total,
            items=[self.to_response(notice, user_id) for notice in records],
        )

    def get_unread_count(self, user_id: int) -> NoticeUnreadCountResponse:
        read_ids = {
            notice_id
            for (notice_id,) in self.db.query(NoticeRead.notice_id).filter(
                NoticeRead.user_id == user_id
            ).all()
        }

        system_ids = [
            notice_id
            for (notice_id,) in self.db.query(Notice.id).filter(
                Notice.type == "system",
                Notice.target_user_id.is_(None),
            ).all()
        ]
        reminder_ids = [
            notice_id
            for (notice_id,) in self.db.query(Notice.id).filter(
                Notice.type == "reminder",
                Notice.target_user_id == user_id,
            ).all()
        ]

        system_unread = sum(1 for notice_id in system_ids if notice_id not in read_ids)
        reminder_unread = sum(1 for notice_id in reminder_ids if notice_id not in read_ids)

        return NoticeUnreadCountResponse(
            total=system_unread + reminder_unread,
            reminder=reminder_unread,
            system=system_unread,
        )

    def get_recent_notifications(
        self,
        user_id: int,
        limit: int = 3,
    ) -> List[NoticeResponse]:
        records = (
            self._build_my_notice_query(user_id)
            .order_by(Notice.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self.to_response(notice, user_id) for notice in records]

    def mark_as_read(self, user_id: int, notice_id: int) -> None:
        existing = self.db.query(NoticeRead).filter(
            NoticeRead.notice_id == notice_id,
            NoticeRead.user_id == user_id,
        ).first()
        if existing:
            return

        self.db.add(NoticeRead(notice_id=notice_id, user_id=user_id))
        self.db.commit()

    def mark_all_as_read(self, user_id: int, tab: Optional[str] = None) -> None:
        read_ids = {
            notice_id
            for (notice_id,) in self.db.query(NoticeRead.notice_id).filter(
                NoticeRead.user_id == user_id
            ).all()
        }
        unread_ids = [
            notice_id
            for (notice_id,) in self._build_my_notice_query(user_id, tab).with_entities(Notice.id).all()
            if notice_id not in read_ids
        ]
        if not unread_ids:
            return

        self.db.bulk_save_objects(
            [NoticeRead(notice_id=notice_id, user_id=user_id) for notice_id in unread_ids]
        )
        self.db.commit()

    def _build_my_notice_query(self, user_id: int, tab: Optional[str] = None):
        query = self.db.query(Notice).options(
            joinedload(Notice.author),
            joinedload(Notice.reads),
        )

        if tab == "reminder":
            return query.filter(
                Notice.type == "reminder",
                Notice.target_user_id == user_id,
            )

        if tab == "system":
            return query.filter(
                Notice.type == "system",
                Notice.target_user_id.is_(None),
            )

        return query.filter(
            or_(
                (Notice.type == "system") & Notice.target_user_id.is_(None),
                (Notice.type == "reminder") & (Notice.target_user_id == user_id),
            )
        )
