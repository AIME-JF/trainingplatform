"""
个人中心控制器
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import ProfileService
from app.schemas import ProfileUpdate
from logger import logger


class ProfileController:
    """个人中心控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ProfileService(db)

    def get_profile(self, user_id: int):
        result = self.service.get_profile(user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return result

    def update_profile(self, user_id: int, data: ProfileUpdate):
        try:
            result = self.service.update_profile(user_id, data)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新个人信息异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新个人信息失败")

    def get_study_stats(self, user_id: int):
        return self.service.get_study_stats(user_id)

    def get_exam_history(self, user_id: int):
        return self.service.get_exam_history(user_id)
