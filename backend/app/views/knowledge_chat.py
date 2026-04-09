"""
知识问答对话路由
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.knowledge_chat import KnowledgeChatController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import KnowledgeChatSessionCreateRequest, StandardResponse, TokenData
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/knowledge-chat", tags=["knowledge_chat"])


def _require_case_access(db: Session, user_id: int, mode: str):
    if mode != "case":
        return
    if is_admin_user(db, user_id) or is_instructor_user(db, user_id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="仅管理员或教官可创建该模式会话",
    )


@router.post("/sessions", response_model=StandardResponse, summary="创建知识问答会话")
def create_session(
    payload: KnowledgeChatSessionCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_case_access(db, current_user.user_id, payload.mode)
    controller = KnowledgeChatController(db)
    data = controller.create_session(
        current_user.user_id,
        payload.knowledge_item_ids,
        payload.mode,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=data)


@router.post("/sessions/{session_id}/messages", response_model=StandardResponse, summary="发送知识问答消息")
def send_message(
    session_id: int,
    content: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = KnowledgeChatController(db)
    data = controller.send_message(
        session_id,
        current_user.user_id,
        content,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=data)


@router.get("/sessions", response_model=StandardResponse, summary="知识问答会话列表")
def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = KnowledgeChatController(db)
    data = controller.list_sessions(current_user.user_id, page, size)
    return StandardResponse(data=data)


@router.get("/sessions/{session_id}", response_model=StandardResponse, summary="知识问答会话详情")
def get_session(
    session_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = KnowledgeChatController(db)
    data = controller.get_session(session_id, current_user.user_id)
    return StandardResponse(data=data)
