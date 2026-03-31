"""
证书管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    CertificateCreate, CertificateResponse
)
from app.controllers import CertificateController

router = APIRouter(prefix="/certificates", tags=["证书管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[CertificateResponse]], summary="证书列表")
def get_certificates(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    user_id: Optional[int] = None,
    training_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取证书列表"""
    controller = CertificateController(db)
    data = controller.get_certificates(page, size, user_id, training_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[CertificateResponse], summary="签发证书")
def create_certificate(
    data: CertificateCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """签发证书"""
    controller = CertificateController(db)
    result = controller.create_certificate(data)
    return StandardResponse(data=result)
