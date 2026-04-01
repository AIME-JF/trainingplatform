"""
培训班类型管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.training_type import TrainingTypeService
from app.schemas.training_type import (
    TrainingTypeCreate, TrainingTypeUpdate, TrainingTypeResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class TrainingTypeController:
    """培训班类型控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TrainingTypeService(db)

    def create_training_type(self, data: TrainingTypeCreate) -> TrainingTypeResponse:
        """创建培训班类型"""
        try:
            return self.service.create_training_type(data)
        except ValueError as e:
            logger.warning(f"创建培训班类型失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建培训班类型异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建培训班类型失败")

    def get_training_type_by_id(self, training_type_id: int) -> TrainingTypeResponse:
        """根据ID获取培训班类型"""
        result = self.service.get_training_type_by_id(training_type_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班类型不存在")
        return result

    def get_training_types(
        self, page: int = 1, size: int = 10,
        name: Optional[str] = None, is_active: Optional[bool] = None
    ) -> PaginatedResponse[TrainingTypeResponse]:
        """获取培训班类型列表"""
        return self.service.get_training_types(page, size, name, is_active)

    def update_training_type(self, training_type_id: int, data: TrainingTypeUpdate) -> TrainingTypeResponse:
        """更新培训班类型"""
        try:
            result = self.service.update_training_type(training_type_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班类型不存在")
            return result
        except ValueError as e:
            logger.warning(f"更新培训班类型失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新培训班类型异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新培训班类型失败")

    def delete_training_type(self, training_type_id: int) -> bool:
        """删除培训班类型"""
        try:
            success = self.service.delete_training_type(training_type_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班类型不存在")
            return success
        except ValueError as e:
            logger.warning(f"删除培训班类型失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除培训班类型异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除培训班类型失败")
