"""
资源审核控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.review import ReviewService
from app.schemas.review import ReviewTaskActionRequest, ReviewPolicyCreate, ReviewPolicyUpdate
from logger import logger


class ReviewController:
    """审核控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ReviewService(db)

    def submit_resource(self, resource_id: int, current_user_id: int):
        try:
            result = self.service.submit_resource(resource_id, current_user_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在')
            return result
        except PermissionError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"提交审核异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='提交审核失败')

    def get_tasks(self, current_user_id: int, status_filter: str = 'pending'):
        try:
            return self.service.list_my_tasks(current_user_id, status_filter)
        except Exception as e:
            logger.error(f"获取审核任务异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='获取审核任务失败')

    def approve_task(self, task_id: int, current_user_id: int, data: ReviewTaskActionRequest):
        try:
            return self.service.approve_task(task_id, current_user_id, data.comment)
        except PermissionError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.db.rollback()
            logger.error(f"审核通过异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='审核通过失败')

    def reject_task(self, task_id: int, current_user_id: int, data: ReviewTaskActionRequest):
        try:
            return self.service.reject_task(task_id, current_user_id, data.comment)
        except PermissionError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.db.rollback()
            logger.error(f"审核驳回异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='审核驳回失败')

    def get_workflow(self, resource_id: int):
        data = self.service.get_workflow(resource_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='审核流程不存在')
        return data

    def get_policies(self):
        try:
            return self.service.list_policies()
        except Exception as e:
            logger.error(f"获取审核策略异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='获取审核策略失败')

    def create_policy(self, data: ReviewPolicyCreate):
        try:
            return self.service.create_policy(data)
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建审核策略异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='创建审核策略失败')

    def update_policy(self, policy_id: int, data: ReviewPolicyUpdate):
        try:
            result = self.service.update_policy(policy_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='审核策略不存在')
            return result
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新审核策略异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='更新审核策略失败')
