"""
个人中心路由
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData,
    ProfileUpdate, ProfileResponse, StudyStatsResponse, ExamHistoryResponse
)
from app.controllers import ProfileController

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=StandardResponse[ProfileResponse], summary="个人信息")
def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取个人信息"""
    controller = ProfileController(db)
    data = controller.get_profile(current_user.user_id)
    return StandardResponse(data=data)


@router.put("", response_model=StandardResponse[ProfileResponse], summary="更新个人信息")
def update_profile(
    data: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新个人信息"""
    controller = ProfileController(db)
    result = controller.update_profile(current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/study-stats", response_model=StandardResponse[StudyStatsResponse], summary="学习统计")
def get_study_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学习统计"""
    controller = ProfileController(db)
    data = controller.get_study_stats(current_user.user_id)
    return StandardResponse(data=data)


@router.get("/exam-history", response_model=StandardResponse[List[ExamHistoryResponse]], summary="考试历史")
def get_exam_history(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试历史"""
    controller = ProfileController(db)
    data = controller.get_exam_history(current_user.user_id)
    return StandardResponse(data=data)
