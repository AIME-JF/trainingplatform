"""
角色管理控制器
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import RoleService
from app.schemas import (
    RoleCreate, RoleUpdate, RoleResponse, RoleSimpleResponse, PaginatedResponse,
    RolePermissionUpdate
)
from logger import logger


class RoleController:
    """角色控制器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.role_service = RoleService(db)
    
    def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """创建角色"""
        try:
            return self.role_service.create_role(role_data)
        except ValueError as e:
            logger.warning(f"创建角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"创建角色异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建角色失败"
            )
    
    def get_role_by_id(self, role_id: int) -> RoleResponse:
        """根据ID获取角色"""
        role = self.role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role
    
    def get_roles(
        self, 
        page: int = 1, 
        size: int = 10,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        order: int = 0
    ) -> PaginatedResponse[RoleSimpleResponse]:
        """获取角色列表"""
        return self.role_service.get_roles(page, size, name, is_active, order)
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> RoleResponse:
        """更新角色"""
        try:
            role = self.role_service.update_role(role_id, role_data)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="角色不存在"
                )
            return role
        except ValueError as e:
            logger.warning(f"更新角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"更新角色异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新角色失败"
            )
    
    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        success = self.role_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return success

    def update_role_permissions(self, role_id: int, permission_data: RolePermissionUpdate) -> RoleResponse:
        """更新角色权限"""
        try:
            role = self.role_service.update_role_permissions(role_id, permission_data)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="角色不存在"
                )
            return role
        except ValueError as e:
            logger.warning(f"更新角色权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"更新角色权限异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新角色权限失败"
            ) 