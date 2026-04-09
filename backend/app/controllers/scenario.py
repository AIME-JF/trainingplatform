"""
场景模拟控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.scenario import ScenarioService
from logger import logger


class ScenarioController:
    """场景模拟控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ScenarioService(db)

    def list_templates(
        self,
        page: int,
        size: int,
        category: Optional[str],
        status_filter: Optional[str],
        user_id: Optional[int],
        *,
        is_admin: bool = False,
    ):
        try:
            return self.service.list_templates(page, size, category, status_filter, user_id, is_admin=is_admin)
        except Exception as exc:
            logger.error("获取场景模板列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取模板列表失败")

    def list_available_templates(self, category: Optional[str]):
        try:
            return self.service.list_available_templates(category)
        except Exception as exc:
            logger.error("获取可用场景模板列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取模板列表失败")

    def get_template(self, template_id: int):
        try:
            result = self.service.get_template(template_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("获取场景模板详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取模板详情失败")

    def create_template(self, data: dict, user_id: int):
        try:
            return self.service.create_template(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建场景模板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建模板失败")

    def update_template(self, template_id: int, data: dict, user_id: int, *, is_admin: bool = False):
        try:
            result = self.service.update_template(template_id, data, user_id, is_admin=is_admin)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在")
            return result
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("更新场景模板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新模板失败")

    def delete_template(self, template_id: int, user_id: int, *, is_admin: bool = False):
        try:
            ok = self.service.delete_template(template_id, user_id, is_admin=is_admin)
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在")
            return {"deleted": True}
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("删除场景模板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除模板失败")

    def publish_template(self, template_id: int, user_id: int, *, is_admin: bool = False):
        try:
            result = self.service.publish_template(template_id, user_id, is_admin=is_admin)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在")
            return result
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("发布场景模板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发布模板失败")

    def start_session(self, template_id: int, user_id: int):
        try:
            return self.service.start_session(template_id, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("开始场景模拟异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="开始模拟失败")

    def send_session_message(self, session_id: int, user_id: int, content: str):
        try:
            return self.service.send_session_message(session_id, user_id, content)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("发送场景模拟消息异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发送消息失败")

    def end_session(self, session_id: int, user_id: int):
        try:
            return self.service.end_session(session_id, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("结束场景模拟异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="结束模拟失败")

    def list_user_sessions(self, user_id: int, page: int, size: int):
        try:
            return self.service.list_user_sessions(user_id, page, size)
        except Exception as exc:
            logger.error("获取用户模拟记录异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取模拟记录失败")

    def list_template_sessions(self, template_id: int, page: int, size: int, user_id: int, *, is_admin: bool = False):
        try:
            return self.service.list_template_sessions(template_id, page, size, user_id, is_admin=is_admin)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except Exception as exc:
            logger.error("获取模板模拟记录异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取模拟记录失败")

    def get_session_detail(self, session_id: int, user_id: int, *, is_admin: bool = False, is_instructor: bool = False):
        try:
            result = self.service.get_session_detail(
                session_id,
                user_id,
                is_admin=is_admin,
                is_instructor=is_instructor,
            )
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟会话不存在")
            return result
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("获取模拟会话详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话详情失败")
