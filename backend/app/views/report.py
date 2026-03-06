"""
数据看板路由
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData,
    KpiResponse, TrendItem, PoliceTypeDistribution, CityRanking
)
from app.controllers import ReportController

router = APIRouter(prefix="/report", tags=["数据看板"])


@router.get("/kpi", response_model=StandardResponse[KpiResponse], summary="KPI数据")
def get_kpi(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取KPI数据"""
    controller = ReportController(db)
    data = controller.get_kpi()
    return StandardResponse(data=data)


@router.get("/trend", response_model=StandardResponse[List[TrendItem]], summary="月度趋势")
def get_trend(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取月度趋势"""
    controller = ReportController(db)
    data = controller.get_trend()
    return StandardResponse(data=data)


@router.get("/police-type-distribution",
            response_model=StandardResponse[List[PoliceTypeDistribution]], summary="警种分布")
def get_police_type_distribution(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取警种分布"""
    controller = ReportController(db)
    data = controller.get_police_type_distribution()
    return StandardResponse(data=data)


@router.get("/city-ranking", response_model=StandardResponse[List[CityRanking]], summary="城市排名")
def get_city_ranking(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取城市排名"""
    controller = ReportController(db)
    data = controller.get_city_ranking()
    return StandardResponse(data=data)
