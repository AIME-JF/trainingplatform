"""
考试管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    ExamCreate, ExamUpdate, ExamResponse, ExamDetailResponse,
    ExamSubmit, ExamRecordResponse
)
from app.controllers import ExamController

router = APIRouter(prefix="/exams", tags=["考试管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[ExamResponse]], summary="考试列表")
def get_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试列表"""
    controller = ExamController(db)
    data = controller.get_exams(page, size, status, type, search)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[ExamResponse], summary="创建考试")
def create_exam(
    data: ExamCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建考试"""
    controller = ExamController(db)
    result = controller.create_exam(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/{exam_id}", response_model=StandardResponse[ExamDetailResponse], summary="考试详情")
def get_exam(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试详情（含题目）"""
    controller = ExamController(db)
    data = controller.get_exam_detail(exam_id)
    return StandardResponse(data=data)


@router.post("/{exam_id}/submit", response_model=StandardResponse[ExamRecordResponse], summary="提交考试")
def submit_exam(
    exam_id: int,
    data: ExamSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交考试"""
    controller = ExamController(db)
    result = controller.submit_exam(exam_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{exam_id}/result", response_model=StandardResponse[ExamRecordResponse], summary="考试结果")
def get_exam_result(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试结果"""
    controller = ExamController(db)
    data = controller.get_exam_result(exam_id, current_user.user_id)
    return StandardResponse(data=data)


@router.get("/{exam_id}/scores", response_model=StandardResponse[PaginatedResponse[ExamRecordResponse]],
            summary="成绩管理")
def get_exam_scores(
    exam_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取成绩列表（教官/管理员）"""
    controller = ExamController(db)
    data = controller.get_exam_scores(exam_id, page, size)
    return StandardResponse(data=data)


@router.get("/{exam_id}/records/analysis", summary="获取考试分析报表")
def get_exam_analysis(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取某场考试的平铺成绩明细，供前端报表展示"""
    controller = ExamController(db)
    data = controller.get_exam_analysis(exam_id)
    return StandardResponse(data=data)
