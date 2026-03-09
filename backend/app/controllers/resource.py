"""
资源库控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.resource import ResourceService
from app.schemas.resource import ResourceCreate, ResourceUpdate
from logger import logger


class ResourceController:
    """资源库控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ResourceService(db)

    def get_resources(self, current_user_id: int, user_permissions: list, page: int = 1, size: int = 10,
                      search: Optional[str] = None, status_filter: Optional[str] = None,
                      content_type: Optional[str] = None, my_only: bool = False):
        try:
            return self.service.get_resources(
                current_user_id=current_user_id,
                user_permissions=user_permissions,
                page=page,
                size=size,
                search=search,
                status=status_filter,
                content_type=content_type,
                my_only=my_only,
            )
        except Exception as e:
            logger.error(f"获取资源列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='获取资源列表失败')

    def create_resource(self, data: ResourceCreate, current_user_id: int):
        try:
            return self.service.create_resource(data, current_user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='创建资源失败')

    def get_resource_by_id(self, resource_id: int, current_user_id: int, user_permissions: list):
        data = self.service.get_resource_by_id(resource_id, current_user_id, user_permissions)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在或无访问权限')
        return data

    def update_resource(self, resource_id: int, data: ResourceUpdate, current_user_id: int, user_permissions: list):
        try:
            result = self.service.update_resource(resource_id, data, current_user_id, user_permissions)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在')
            return result
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='更新资源失败')

    def publish_resource(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            result = self.service.publish_resource(
                resource_id=resource_id,
                current_user_id=current_user_id,
                user_permissions=user_permissions,
                force=False,
            )
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在')
            return result
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"发布资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='发布资源失败')

    def offline_resource(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            result = self.service.offline_resource(
                resource_id=resource_id,
                current_user_id=current_user_id,
                user_permissions=user_permissions,
                force=False,
            )
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在')
            return result
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"下线资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='下线资源失败')
