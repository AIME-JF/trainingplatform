"""
工作台控制器
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import DashboardService
from logger import logger


class DashboardController:
    """工作台控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = DashboardService(db)

    def get_dashboard(self, user_id: int, role: str):
        try:
            return self.service.get_dashboard(user_id, role)
        except Exception as e:
            logger.error(f"获取工作台数据异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取工作台数据失败")
