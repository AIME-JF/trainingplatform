"""
资源评论控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.resource import ResourceCommentCreate
from app.services.resource_comment import ResourceCommentService
from logger import logger


class ResourceCommentController:
    """资源评论控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ResourceCommentService(db)

    def list_comments(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            return self.service.list_comments(resource_id, current_user_id, user_permissions)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error(f"获取资源评论异常: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='获取资源评论失败')

    def create_comment(self, resource_id: int, current_user_id: int, user_permissions: list, data: ResourceCommentCreate):
        try:
            return self.service.create_comment(resource_id, current_user_id, user_permissions, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error(f"创建资源评论异常: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='发表评论失败')

    def delete_comment(self, resource_id: int, comment_id: int, current_user_id: int, user_permissions: list):
        try:
            ok = self.service.delete_comment(resource_id, comment_id, current_user_id, user_permissions)
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='评论不存在')
            return {'success': True}
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"删除资源评论异常: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='删除评论失败')
