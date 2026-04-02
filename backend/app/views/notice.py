"""
公告管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse, NoticeUnreadCountResponse
from app.models import Notice, NoticeRead

router = APIRouter(prefix="/notices", tags=["notice_management"])


def _to_response(notice: Notice, user_id: Optional[int] = None) -> NoticeResponse:
    is_read = False
    if user_id and hasattr(notice, 'reads'):
        is_read = any(r.user_id == user_id for r in (notice.reads or []))
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


@router.get("/my", response_model=StandardResponse[PaginatedResponse[NoticeResponse]], summary="我的通知")
def get_my_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tab: Optional[str] = Query(None, description="标签页: reminder/system，不传返回全部"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的通知列表（系统公告 + 定向提醒）"""
    query = db.query(Notice).options(joinedload(Notice.author), joinedload(Notice.reads))

    if tab == "reminder":
        query = query.filter(
            Notice.type == "reminder",
            Notice.target_user_id == current_user.user_id,
        )
    elif tab == "system":
        query = query.filter(
            Notice.type == "system",
            Notice.target_user_id.is_(None),
        )
    else:
        # 全部：系统公告（无 target）+ 发给我的提醒
        query = query.filter(
            or_(
                (Notice.type == "system") & Notice.target_user_id.is_(None),
                (Notice.type == "reminder") & (Notice.target_user_id == current_user.user_id),
            )
        )

    total = query.count()
    skip = (page - 1) * size
    records = query.order_by(Notice.created_at.desc()).offset(skip).limit(size).all()

    items = [_to_response(n, current_user.user_id) for n in records]

    return StandardResponse(data=PaginatedResponse(
        page=page, size=size, total=total, items=items,
    ))


@router.get("/unread-count", response_model=StandardResponse[NoticeUnreadCountResponse], summary="未读通知计数")
def get_unread_count(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的未读通知计数"""
    read_ids = {
        r.notice_id
        for r in db.query(NoticeRead.notice_id).filter(NoticeRead.user_id == current_user.user_id).all()
    }

    # System notices (no target)
    system_notices = db.query(Notice.id).filter(
        Notice.type == "system",
        Notice.target_user_id.is_(None),
    ).all()
    system_unread = sum(1 for (nid,) in system_notices if nid not in read_ids)

    # Reminders for me
    reminder_notices = db.query(Notice.id).filter(
        Notice.type == "reminder",
        Notice.target_user_id == current_user.user_id,
    ).all()
    reminder_unread = sum(1 for (nid,) in reminder_notices if nid not in read_ids)

    return StandardResponse(data=NoticeUnreadCountResponse(
        total=system_unread + reminder_unread,
        reminder=reminder_unread,
        system=system_unread,
    ))


@router.post("/{notice_id}/read", response_model=StandardResponse, summary="标记通知为已读")
def mark_as_read(
    notice_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单条通知为已读"""
    existing = db.query(NoticeRead).filter(
        NoticeRead.notice_id == notice_id,
        NoticeRead.user_id == current_user.user_id,
    ).first()
    if not existing:
        db.add(NoticeRead(notice_id=notice_id, user_id=current_user.user_id))
        db.commit()
    return StandardResponse(message="已读")


@router.post("/read-all", response_model=StandardResponse, summary="全部标记已读")
def mark_all_as_read(
    tab: Optional[str] = Query(None, description="标签页: reminder/system，不传则全部标记"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将当前用户的通知全部标记为已读"""
    read_ids = {
        r.notice_id
        for r in db.query(NoticeRead.notice_id).filter(NoticeRead.user_id == current_user.user_id).all()
    }

    query = db.query(Notice.id)
    if tab == "reminder":
        query = query.filter(Notice.type == "reminder", Notice.target_user_id == current_user.user_id)
    elif tab == "system":
        query = query.filter(Notice.type == "system", Notice.target_user_id.is_(None))
    else:
        query = query.filter(
            or_(
                (Notice.type == "system") & Notice.target_user_id.is_(None),
                (Notice.type == "reminder") & (Notice.target_user_id == current_user.user_id),
            )
        )

    unread_ids = [nid for (nid,) in query.all() if nid not in read_ids]
    if unread_ids:
        db.bulk_save_objects([NoticeRead(notice_id=nid, user_id=current_user.user_id) for nid in unread_ids])
        db.commit()

    return StandardResponse(message="已全部标记为已读")


@router.get("", response_model=StandardResponse[PaginatedResponse[NoticeResponse]], summary="公告列表")
def get_notices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    type: Optional[str] = Query(None, description="类型: system/training/reminder"),
    training_id: Optional[int] = Query(None, description="培训班ID(获取培训班公告)"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取公告列表。type=system 系统公告；type=training + training_id 培训班公告"""
    query = db.query(Notice).options(joinedload(Notice.author))

    if type:
        query = query.filter(Notice.type == type)
    if training_id is not None:
        query = query.filter(Notice.training_id == training_id)

    total = query.count()
    query = query.order_by(Notice.created_at.desc())

    if size == -1:
        records = query.all()
    else:
        skip = (page - 1) * size
        records = query.offset(skip).limit(size).all()

    items = [_to_response(n) for n in records]

    return StandardResponse(data=PaginatedResponse(
        page=page,
        size=size if size != -1 else total,
        total=total,
        items=items
    ))


@router.post("", response_model=StandardResponse[NoticeResponse], summary="创建公告")
def create_notice(
    data: NoticeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建公告（系统公告、培训班公告或提醒通知）"""
    notice = Notice(
        title=data.title,
        content=data.content,
        type=data.type,
        training_id=data.training_id if data.type == 'training' else None,
        target_user_id=data.target_user_id if data.type == 'reminder' else None,
        reminder_type=data.reminder_type if data.type == 'reminder' else None,
        author_id=current_user.user_id
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return StandardResponse(data=_to_response(notice))


@router.put("/{notice_id}", response_model=StandardResponse[NoticeResponse], summary="更新公告")
def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新公告"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return StandardResponse(code=404, message="公告不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notice, field, value)

    db.commit()
    db.refresh(notice)
    return StandardResponse(data=_to_response(notice))


@router.delete("/{notice_id}", response_model=StandardResponse, summary="删除公告")
def delete_notice(
    notice_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除公告"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return StandardResponse(code=404, message="公告不存在")

    db.delete(notice)
    db.commit()
    return StandardResponse(message="删除成功")
