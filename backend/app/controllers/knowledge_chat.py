"""
知识问答对话控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.knowledge_chat import KnowledgeChatService
from logger import logger


class KnowledgeChatController:
    """知识问答对话控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = KnowledgeChatService(db)

    def create_session(self, user_id: int, knowledge_item_ids: list[int], mode: str, *, is_admin: bool = False):
        try:
            return self.service.create_session(user_id, knowledge_item_ids, mode, is_admin=is_admin)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建知识问答会话异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建会话失败")

    def send_message(self, session_id: int, user_id: int, content: str, *, is_admin: bool = False):
        try:
            return self.service.send_message(session_id, user_id, content, is_admin=is_admin)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("发送知识问答消息异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发送消息失败")

    def list_sessions(self, user_id: int, page: int, size: int):
        try:
            return self.service.list_sessions(user_id, page, size)
        except Exception as exc:
            logger.error("获取知识问答会话列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话列表失败")

    def get_session(self, session_id: int, user_id: int):
        try:
            result = self.service.get_session(session_id, user_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("获取知识问答会话详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话详情失败")
