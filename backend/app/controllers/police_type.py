"""
警种管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import PoliceTypeService
from app.schemas import (
    PoliceTypeCreate, PoliceTypeUpdate, PoliceTypeSimpleResponse, PaginatedResponse
)
from logger import logger


class PoliceTypeController:
    """警种控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = PoliceTypeService(db)

    def create_police_type(self, data: PoliceTypeCreate) -> PoliceTypeSimpleResponse:
        """创建警种"""
        try:
            return self.service.create_police_type(data)
        except ValueError as e:
            logger.warning(f"创建警种失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建警种异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建警种失败")

    def get_police_type_by_id(self, police_type_id: int) -> PoliceTypeSimpleResponse:
        """根据ID获取警种"""
        result = self.service.get_police_type_by_id(police_type_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="警种不存在")
        return result

    def get_police_types(
        self, page: int = 1, size: int = 10,
        name: Optional[str] = None, is_active: Optional[bool] = None
    ) -> PaginatedResponse[PoliceTypeSimpleResponse]:
        """获取警种列表"""
        return self.service.get_police_types(page, size, name, is_active)

    def update_police_type(self, police_type_id: int, data: PoliceTypeUpdate) -> PoliceTypeSimpleResponse:
        """更新警种"""
        try:
            result = self.service.update_police_type(police_type_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="警种不存在")
            return result
        except ValueError as e:
            logger.warning(f"更新警种失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新警种异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新警种失败")

    def delete_police_type(self, police_type_id: int) -> bool:
        """删除警种"""
        try:
            success = self.service.delete_police_type(police_type_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="警种不存在")
            return success
        except ValueError as e:
            logger.warning(f"删除警种失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除警种异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除警种失败")
