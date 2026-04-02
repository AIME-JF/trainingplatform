"""
公告管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse, NoticeUnreadCountResponse
from app.models import Notice
from app.services.notice import NoticeService

router = APIRouter(prefix="/notices", tags=["notice_management"])


@router.get("/my", response_model=StandardResponse[PaginatedResponse[NoticeResponse]], summary="我的通知")
def get_my_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tab: Optional[str] = Query(None, description="标签页: reminder/system，不传返回全部"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的通知列表（系统公告 + 定向提醒）"""
    service = NoticeService(db)
    return StandardResponse(data=service.get_my_notifications(current_user.user_id, page, size, tab))


@router.get("/unread-count", response_model=StandardResponse[NoticeUnreadCountResponse], summary="未读通知计数")
def get_unread_count(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的未读通知计数"""
    service = NoticeService(db)
    return StandardResponse(data=service.get_unread_count(current_user.user_id))


@router.post("/{notice_id}/read", response_model=StandardResponse, summary="标记通知为已读")
def mark_as_read(
    notice_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单条通知为已读"""
    service = NoticeService(db)
    service.mark_as_read(current_user.user_id, notice_id)
    return StandardResponse(message="已读")


@router.post("/read-all", response_model=StandardResponse, summary="全部标记已读")
def mark_all_as_read(
    tab: Optional[str] = Query(None, description="标签页: reminder/system，不传则全部标记"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将当前用户的通知全部标记为已读"""
    service = NoticeService(db)
    service.mark_all_as_read(current_user.user_id, tab)
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

    service = NoticeService(db)
    items = [service.to_response(n) for n in records]

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
    service = NoticeService(db)
    return StandardResponse(data=service.to_response(notice))


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
    service = NoticeService(db)
    return StandardResponse(data=service.to_response(notice))


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
