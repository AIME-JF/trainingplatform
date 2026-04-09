"""
Library routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import LibraryController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    LibraryBatchFileCreateRequest,
    LibraryDashboardResponse,
    LibraryFolderCreate,
    LibraryFolderResponse,
    LibraryFolderUpdate,
    LibraryItemDetailResponse,
    LibraryItemListParams,
    LibraryItemListResponse,
    LibraryItemMoveRequest,
    LibraryItemUpdateRequest,
    LibraryKnowledgeCreateRequest,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)
from app.utils.authz import is_admin_user

router = APIRouter(prefix="/library", tags=["library_management"])


def _resolve_library_admin_access(db: Session, current_user: TokenData) -> bool:
    return is_admin_user(db, current_user.user_id)


@router.get("/dashboard", response_model=StandardResponse[LibraryDashboardResponse], summary="获取管理员知识库数据看板")
def get_library_dashboard(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可查看知识库数据看板")
    controller = LibraryController(db)
    return StandardResponse(data=controller.get_admin_dashboard())


@router.get("/folders", response_model=StandardResponse[list[LibraryFolderResponse]], summary="获取知识库文件夹树")
def get_library_folders(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = LibraryController(db)
    return StandardResponse(data=controller.list_folders(current_user.user_id))


@router.post("/folders", response_model=StandardResponse[LibraryFolderResponse], summary="创建知识库文件夹")
def create_library_folder(
    data: LibraryFolderCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = LibraryController(db)
    return StandardResponse(data=controller.create_folder(current_user.user_id, data))


@router.put("/folders/{folder_id}", response_model=StandardResponse[LibraryFolderResponse], summary="更新知识库文件夹")
def update_library_folder(
    folder_id: int,
    data: LibraryFolderUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = LibraryController(db)
    return StandardResponse(data=controller.update_folder(folder_id, current_user.user_id, data))


@router.delete("/folders/{folder_id}", response_model=StandardResponse, summary="删除知识库文件夹")
def delete_library_folder(
    folder_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = LibraryController(db)
    controller.delete_folder(folder_id, current_user.user_id)
    return StandardResponse(message="文件夹已删除")


@router.get("/items", response_model=StandardResponse[PaginatedResponse[LibraryItemListResponse]], summary="获取知识库资源列表")
def get_library_items(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=-1),
    scope: str = Query("private"),
    category: Optional[str] = Query(None),
    folder_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    source_kind: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    params = LibraryItemListParams(
        scope=scope,
        category=category,
        folder_id=folder_id,
        search=search,
        source_kind=source_kind,
    )
    return StandardResponse(data=controller.list_items(current_user.user_id, params, page, size, is_admin=is_admin))


@router.get("/assistant-items", response_model=StandardResponse[list[LibraryItemListResponse]], summary="获取知识助手可选资源")
def get_library_assistant_items(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.list_assistant_items(current_user.user_id, is_admin=is_admin))


@router.get("/items/{item_id}", response_model=StandardResponse[LibraryItemDetailResponse], summary="获取资源详情")
def get_library_item_detail(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.get_item_detail(item_id, current_user.user_id, is_admin=is_admin))


@router.post("/items/files", response_model=StandardResponse[list[LibraryItemDetailResponse]], summary="批量创建文件资源")
def create_library_items_from_files(
    data: LibraryBatchFileCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.create_items_from_files(current_user.user_id, data, is_admin=is_admin))


@router.post("/items/knowledge", response_model=StandardResponse[LibraryItemDetailResponse], summary="创建知识点卡片")
def create_library_knowledge_item(
    data: LibraryKnowledgeCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = LibraryController(db)
    return StandardResponse(data=controller.create_knowledge_item(current_user.user_id, data))


@router.put("/items/{item_id}", response_model=StandardResponse[LibraryItemDetailResponse], summary="更新知识库资源")
def update_library_item(
    item_id: int,
    data: LibraryItemUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.update_item(item_id, current_user.user_id, data, is_admin=is_admin))


@router.post("/items/{item_id}/move", response_model=StandardResponse[LibraryItemDetailResponse], summary="移动知识库资源")
def move_library_item(
    item_id: int,
    data: LibraryItemMoveRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.move_item(item_id, current_user.user_id, data, is_admin=is_admin))


@router.post("/items/{item_id}/share", response_model=StandardResponse[LibraryItemDetailResponse], summary="公开知识库资源")
def share_library_item(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.share_item(item_id, current_user.user_id, True, is_admin=is_admin))


@router.post("/items/{item_id}/unshare", response_model=StandardResponse[LibraryItemDetailResponse], summary="取消公开知识库资源")
def unshare_library_item(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    return StandardResponse(data=controller.share_item(item_id, current_user.user_id, False, is_admin=is_admin))


@router.delete("/items/{item_id}", response_model=StandardResponse, summary="删除知识库资源")
def delete_library_item(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _resolve_library_admin_access(db, current_user)
    controller = LibraryController(db)
    controller.delete_item(item_id, current_user.user_id, is_admin=is_admin)
    return StandardResponse(message="资源已删除")
