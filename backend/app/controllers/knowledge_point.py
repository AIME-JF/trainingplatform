"""
知识点管理控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services import KnowledgePointService
from app.schemas import KnowledgePointCreate, KnowledgePointUpdate
from logger import logger


class KnowledgePointController:
    """知识点控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = KnowledgePointService(db)

    def get_knowledge_points(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        try:
            return self.service.get_knowledge_points(page, size, search, is_active)
        except Exception as exc:
            logger.error("获取知识点列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取知识点列表失败")

    def create_knowledge_point(self, data: KnowledgePointCreate, user_id: int):
        try:
            return self.service.create_knowledge_point(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建知识点异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建知识点失败")

    def update_knowledge_point(self, knowledge_point_id: int, data: KnowledgePointUpdate):
        try:
            result = self.service.update_knowledge_point(knowledge_point_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")
            return result
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("更新知识点异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新知识点失败")

    def delete_knowledge_point(self, knowledge_point_id: int):
        try:
            if not self.service.delete_knowledge_point(knowledge_point_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")
            return True
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("删除知识点异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除知识点失败")
