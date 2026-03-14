"""
培训基地控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.training import TrainingBaseCreate, TrainingBaseUpdate
from app.services.training_base import TrainingBaseService
from logger import logger


class TrainingBaseController:
    """培训基地控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TrainingBaseService(db)

    def get_training_bases(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_training_bases(page, size, search, department_id, current_user_id)
        except Exception as exc:
            logger.error("获取培训基地列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取培训基地列表失败")

    def get_training_base_by_id(self, training_base_id: int, current_user_id: Optional[int] = None):
        result = self.service.get_training_base_by_id(training_base_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训基地不存在")
        return result

    def create_training_base(self, data: TrainingBaseCreate, user_id: Optional[int] = None):
        try:
            return self.service.create_training_base(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建培训基地异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建培训基地失败")

    def update_training_base(self, training_base_id: int, data: TrainingBaseUpdate, user_id: Optional[int] = None):
        try:
            if user_id and "department_id" in data.model_fields_set:
                self.service._ensure_actor_can_assign_training_base_scope(user_id, data.department_id)
            result = self.service.update_training_base(training_base_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训基地不存在")
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新培训基地异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新培训基地失败")

    def delete_training_base(self, training_base_id: int):
        try:
            if not self.service.delete_training_base(training_base_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训基地不存在")
            return True
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("删除培训基地异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除培训基地失败")
