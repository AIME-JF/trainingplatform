"""
工作台路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData, DashboardResponse
from app.controllers import DashboardController

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=StandardResponse[DashboardResponse], summary="获取工作台数据")
def get_dashboard(
    role: str = "student",
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据角色返回不同工作台数据"""
    controller = DashboardController(db)
    data = controller.get_dashboard(current_user.user_id, role)
    return StandardResponse(data=data)
