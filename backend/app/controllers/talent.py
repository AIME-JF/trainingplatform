"""
人才库控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import TalentService
from logger import logger


class TalentController:
    """人才库控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = TalentService(db)

    def get_talents(self, page: int = 1, size: int = 10,
                    search: Optional[str] = None, tier: Optional[str] = None,
                    unit: Optional[str] = None):
        try:
            return self.service.get_talents(page, size, search, tier, unit)
        except Exception as e:
            logger.error(f"获取人才列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取人才列表失败")

    def get_stats(self):
        try:
            return self.service.get_stats()
        except Exception as e:
            logger.error(f"获取人才统计异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取人才统计失败")
