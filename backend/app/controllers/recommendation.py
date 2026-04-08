"""
资源推荐控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.recommendation import RecommendationService
from app.schemas.recommendation import ResourceBehaviorEventCreate
from logger import logger


class RecommendationController:
    """推荐控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = RecommendationService(db)

    def record_event(self, resource_id: int, current_user_id: int, user_permissions: list, data: ResourceBehaviorEventCreate):
        try:
            return self.service.record_event(
                resource_id=resource_id,
                user_id=current_user_id,
                user_permissions=user_permissions,
                event_type=data.event_type,
                watch_seconds=data.watch_seconds,
                context_json=data.context_json,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"记录行为事件异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='记录行为事件失败')

    def get_feed(self, current_user_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_recommendation_feed(current_user_id, page, size)
        except Exception as e:
            logger.error(f"获取推荐流异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='获取推荐流失败')

    def get_community_board_dashboard(self, current_user_id: int, user_permissions: list, range_key: str = '7d'):
        try:
            return self.service.get_community_board_dashboard(current_user_id, user_permissions, range_key)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"鑾峰彇绀惧尯鐪嬫澘寮傚父: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='鑾峰彇绀惧尯鐪嬫澘澶辫触')

    def like_resource(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            return self.service.like_resource(resource_id, current_user_id, user_permissions)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"点赞资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='点赞失败')

    def unlike_resource(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            return self.service.unlike_resource(resource_id, current_user_id, user_permissions)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"取消点赞资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='取消点赞失败')

    def share_resource(self, resource_id: int, current_user_id: int, user_permissions: list):
        try:
            return self.service.share_resource(resource_id, current_user_id, user_permissions)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"转发资源异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='转发失败')
