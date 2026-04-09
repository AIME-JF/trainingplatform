"""
知识库管理控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.knowledge_base import KnowledgeBaseService
from logger import logger


class KnowledgeBaseController:
    """知识库管理控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = KnowledgeBaseService(db)

    # ==================== 知识库 ====================

    def list_knowledge_bases(self, page: int, size: int, visibility: Optional[str], user_role: str):
        try:
            return self.service.list_knowledge_bases(page, size, visibility, user_role)
        except Exception as exc:
            logger.error("获取知识库列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取知识库列表失败")

    def get_knowledge_base(self, kb_id: int):
        try:
            result = self.service.get_knowledge_base(kb_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("获取知识库详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取知识库详情失败")

    def create_knowledge_base(self, name: str, description: Optional[str], visibility: str, user_id: int):
        try:
            return self.service.create_knowledge_base(name, description, visibility, user_id)
        except Exception as exc:
            logger.error("创建知识库异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建知识库失败")

    def update_knowledge_base(self, kb_id: int, name: Optional[str], description: Optional[str], visibility: Optional[str]):
        try:
            result = self.service.update_knowledge_base(kb_id, name, description, visibility)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("更新知识库异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新知识库失败")

    def delete_knowledge_base(self, kb_id: int):
        try:
            ok = self.service.delete_knowledge_base(kb_id)
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
            return {"deleted": True}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("删除知识库异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除知识库失败")

    # ==================== 文档 ====================

    def list_documents(self, kb_id: int, page: int, size: int, search: Optional[str]):
        try:
            return self.service.list_documents(kb_id, page, size, search)
        except Exception as exc:
            logger.error("获取知识库文档列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取文档列表失败")

    def create_document(self, kb_id: int, title: str, content: str, source_type: str, user_id: int):
        try:
            return self.service.create_document(kb_id, title, content, source_type, user_id)
        except Exception as exc:
            logger.error("创建知识库文档异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建文档失败")

    def update_document(self, doc_id: int, title: Optional[str], content: Optional[str]):
        try:
            result = self.service.update_document(doc_id, title, content)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("更新知识库文档异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新文档失败")

    def delete_document(self, doc_id: int):
        try:
            ok = self.service.delete_document(doc_id)
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
            return {"deleted": True}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("删除知识库文档异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除文档失败")
