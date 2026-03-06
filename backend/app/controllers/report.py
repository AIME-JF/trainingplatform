"""
数据看板控制器
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import ReportService
from logger import logger


class ReportController:
    """数据看板控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ReportService(db)

    def get_kpi(self):
        try:
            return self.service.get_kpi()
        except Exception as e:
            logger.error(f"获取KPI数据异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取KPI数据失败")

    def get_trend(self):
        try:
            return self.service.get_trend()
        except Exception as e:
            logger.error(f"获取趋势数据异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取趋势数据失败")

    def get_police_type_distribution(self):
        try:
            return self.service.get_police_type_distribution()
        except Exception as e:
            logger.error(f"获取警种分布异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取警种分布失败")

    def get_city_ranking(self):
        try:
            return self.service.get_city_ranking()
        except Exception as e:
            logger.error(f"获取城市排名异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取城市排名失败")
