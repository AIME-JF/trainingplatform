"""
权限管理控制器
"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import PermissionService
from app.schemas import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PaginatedResponse
)
from logger import logger


class PermissionController:
    """权限控制器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.permission_service = PermissionService(db)
    
    def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """创建权限"""
        try:
            return self.permission_service.create_permission(permission_data)
        except ValueError as e:
            logger.warning(f"创建权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"创建权限异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建权限失败"
            )
    
    def get_permission_by_id(self, permission_id: int) -> PermissionResponse:
        """根据ID获取权限"""
        permission = self.permission_service.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        return permission
    
    def get_permissions(self, page: int = 1, size: int = 10) -> PaginatedResponse[PermissionResponse]:
        """获取权限列表"""
        return self.permission_service.get_permissions(page, size)
    
    def update_permission(self, permission_id: int, permission_data: PermissionUpdate) -> PermissionResponse:
        """更新权限"""
        try:
            permission = self.permission_service.update_permission(permission_id, permission_data)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="权限不存在"
                )
            return permission
        except ValueError as e:
            logger.warning(f"更新权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"更新权限异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新权限失败"
            )
    
    def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""
        success = self.permission_service.delete_permission(permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        return success
    
    def sync_permissions(self, permissions_data: List[dict]) -> List[PermissionResponse]:
        """同步权限"""
        try:
            return self.permission_service.sync_permissions(permissions_data)
        except Exception as e:
            logger.error(f"同步权限异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="同步权限失败"
            ) 