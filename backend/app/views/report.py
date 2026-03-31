"""
数据看板路由
"""
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData,
    KpiResponse, TrendItem, PoliceTypeDistribution, CityRanking,
    TrainingTrendItem, CityAttendanceItem, CityCompletionItem
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


@router.get("/training-trend", response_model=StandardResponse[List[TrainingTrendItem]], summary="培训完成率趋势")
def get_training_trend(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取近6月培训完成率趋势"""
    controller = ReportController(db)
    data = controller.get_training_trend()
    return StandardResponse(data=data)


@router.get("/training-city-attendance", response_model=StandardResponse[List[CityAttendanceItem]], summary="各市参训人数")
def get_training_city_attendance(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取各市局本月参训人数"""
    controller = ReportController(db)
    data = controller.get_training_city_attendance()
    return StandardResponse(data=data)


@router.get("/training-city-completion", response_model=StandardResponse[List[CityCompletionItem]], summary="各市培训完成率")
def get_training_city_completion(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取各市培训完成率排名"""
    controller = ReportController(db)
    data = controller.get_training_city_completion()
    return StandardResponse(data=data)


@router.get("/export", summary="导出报告")
def export_report(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出培训看板 Excel 报告"""
    controller = ReportController(db)
    data = controller.export_report()
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=training_report.xlsx"}
    )


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
