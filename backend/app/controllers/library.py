"""
资源库模块控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.library import (
    LibraryBatchFileCreateRequest,
    LibraryFolderCreate,
    LibraryFolderUpdate,
    LibraryItemListParams,
    LibraryItemMoveRequest,
    LibraryItemUpdateRequest,
    LibraryKnowledgeCreateRequest,
)
from app.services.library import LibraryService


class LibraryController:
    """资源库控制器"""

    def __init__(self, db: Session):
        self.service = LibraryService(db)

    def _handle_value_error(self, action: str, error: Exception):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    def list_folders(self, current_user_id: int):
        return self.service.list_folders(current_user_id)

    def create_folder(self, current_user_id: int, data: LibraryFolderCreate):
        try:
            return self.service.create_folder(current_user_id, data)
        except ValueError as error:
            self._handle_value_error("create_folder", error)

    def update_folder(self, folder_id: int, current_user_id: int, data: LibraryFolderUpdate):
        try:
            return self.service.update_folder(folder_id, current_user_id, data)
        except ValueError as error:
            self._handle_value_error("update_folder", error)

    def delete_folder(self, folder_id: int, current_user_id: int):
        try:
            self.service.delete_folder(folder_id, current_user_id)
            return {"success": True}
        except ValueError as error:
            self._handle_value_error("delete_folder", error)

    def list_items(self, current_user_id: int, params: LibraryItemListParams, page: int, size: int):
        return self.service.list_items(current_user_id, params, page=page, size=size)

    def get_item_detail(self, item_id: int, current_user_id: int, is_admin: bool = False):
        data = self.service.get_item_detail(item_id, current_user_id, is_admin=is_admin)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在或无权限查看")
        return data

    def create_items_from_files(self, current_user_id: int, data: LibraryBatchFileCreateRequest, is_admin: bool = False):
        try:
            return self.service.create_items_from_files(current_user_id, data, is_admin=is_admin)
        except ValueError as error:
            self._handle_value_error("create_items_from_files", error)

    def create_knowledge_item(self, current_user_id: int, data: LibraryKnowledgeCreateRequest):
        try:
            return self.service.create_knowledge_item(current_user_id, data)
        except ValueError as error:
            self._handle_value_error("create_knowledge_item", error)

    def update_item(self, item_id: int, current_user_id: int, data: LibraryItemUpdateRequest, is_admin: bool = False):
        try:
            return self.service.update_item(item_id, current_user_id, data, is_admin=is_admin)
        except ValueError as error:
            self._handle_value_error("update_item", error)

    def move_item(self, item_id: int, current_user_id: int, data: LibraryItemMoveRequest, is_admin: bool = False):
        try:
            return self.service.move_item(item_id, current_user_id, data, is_admin=is_admin)
        except ValueError as error:
            self._handle_value_error("move_item", error)

    def share_item(self, item_id: int, current_user_id: int, is_public: bool, is_admin: bool = False):
        try:
            return self.service.share_item(item_id, current_user_id, is_public=is_public, is_admin=is_admin)
        except ValueError as error:
            self._handle_value_error("share_item", error)

    def delete_item(self, item_id: int, current_user_id: int, is_admin: bool = False):
        try:
            self.service.delete_item(item_id, current_user_id, is_admin=is_admin)
            return {"success": True}
        except ValueError as error:
            self._handle_value_error("delete_item", error)
