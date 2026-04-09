"""
知识库管理路由
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.knowledge_base import KnowledgeBaseController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge_base"])


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行该操作")


# ==================== 知识库 ====================


@router.get("", response_model=StandardResponse, summary="知识库列表")
def list_knowledge_bases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    visibility: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_role = "admin" if is_admin_user(db, current_user.user_id) else (
        "instructor" if is_instructor_user(db, current_user.user_id) else "student"
    )
    controller = KnowledgeBaseController(db)
    data = controller.list_knowledge_bases(page, size, visibility, user_role)
    return StandardResponse(data=data)


@router.get("/{kb_id}", response_model=StandardResponse, summary="知识库详情")
def get_knowledge_base(
    kb_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = KnowledgeBaseController(db)
    data = controller.get_knowledge_base(kb_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse, summary="创建知识库")
def create_knowledge_base(
    name: str = Body(...),
    description: Optional[str] = Body(None),
    visibility: str = Body("all"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.create_knowledge_base(name, description, visibility, current_user.user_id)
    return StandardResponse(data=data)


@router.put("/{kb_id}", response_model=StandardResponse, summary="更新知识库")
def update_knowledge_base(
    kb_id: int,
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    visibility: Optional[str] = Body(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.update_knowledge_base(kb_id, name, description, visibility)
    return StandardResponse(data=data)


@router.delete("/{kb_id}", response_model=StandardResponse, summary="删除知识库")
def delete_knowledge_base(
    kb_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.delete_knowledge_base(kb_id)
    return StandardResponse(data=data)


# ==================== 知识库文档 ====================


@router.get("/{kb_id}/documents", response_model=StandardResponse, summary="知识库文档列表")
def list_documents(
    kb_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    search: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.list_documents(kb_id, page, size, search)
    return StandardResponse(data=data)


@router.post("/{kb_id}/documents", response_model=StandardResponse, summary="创建知识库文档")
def create_document(
    kb_id: int,
    title: str = Body(...),
    content: str = Body(...),
    source_type: str = Body("manual"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.create_document(kb_id, title, content, source_type, current_user.user_id)
    return StandardResponse(data=data)


@router.put("/documents/{doc_id}", response_model=StandardResponse, summary="更新知识库文档")
def update_document(
    doc_id: int,
    title: Optional[str] = Body(None),
    content: Optional[str] = Body(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.update_document(doc_id, title, content)
    return StandardResponse(data=data)


@router.delete("/documents/{doc_id}", response_model=StandardResponse, summary="删除知识库文档")
def delete_document(
    doc_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = KnowledgeBaseController(db)
    data = controller.delete_document(doc_id)
    return StandardResponse(data=data)
