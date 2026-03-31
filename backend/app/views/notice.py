"""
公告管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.models import Notice

router = APIRouter(prefix="/notices", tags=["notice_management"])


def _to_response(notice: Notice) -> NoticeResponse:
    return NoticeResponse(
        id=notice.id,
        title=notice.title,
        content=notice.content,
        type=notice.type,
        training_id=notice.training_id,
        author_id=notice.author_id,
        author_name=notice.author.nickname if notice.author else None,
        created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.get("", response_model=StandardResponse[PaginatedResponse[NoticeResponse]], summary="公告列表")
def get_notices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    type: Optional[str] = Query(None, description="类型: system/training"),
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
    """创建公告（系统公告或培训班公告）"""
    notice = Notice(
        title=data.title,
        content=data.content,
        type=data.type,
        training_id=data.training_id if data.type == 'training' else None,
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
