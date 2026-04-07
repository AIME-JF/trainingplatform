"""
培训计划管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.training_plan import TrainingPlanService
from app.schemas.training_plan import TrainingPlanCreate, TrainingPlanUpdate
from logger import logger


class TrainingPlanController:
    """培训计划控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TrainingPlanService(db)

    def get_list(self, page: int = 1, size: int = 10, year: Optional[str] = None, search: Optional[str] = None):
        try:
            return self.service.get_list(page, size, year, search)
        except Exception as e:
            logger.error(f"获取培训计划列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取培训计划列表失败")

    def get_by_id(self, plan_id: int):
        result = self.service.get_by_id(plan_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训计划不存在")
        return result

    def create(self, data: TrainingPlanCreate, user_id: int):
        try:
            return self.service.create(data, user_id)
        except Exception as e:
            logger.error(f"创建培训计划异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建培训计划失败")

    def update(self, plan_id: int, data: TrainingPlanUpdate):
        result = self.service.update(plan_id, data)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训计划不存在")
        return result

    def delete(self, plan_id: int):
        if not self.service.delete(plan_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训计划不存在")
        return {"message": "删除成功"}
