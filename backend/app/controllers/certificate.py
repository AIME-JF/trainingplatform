"""
证书管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import CertificateService
from app.schemas import CertificateCreate, PaginatedResponse
from logger import logger


class CertificateController:
    """证书控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = CertificateService(db)

    def get_certificates(self, page: int = 1, size: int = 10,
                         user_id: Optional[int] = None, training_id: Optional[int] = None):
        try:
            return self.service.get_certificates(page, size, user_id, training_id)
        except Exception as e:
            logger.error(f"获取证书列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取证书列表失败")

    def create_certificate(self, data: CertificateCreate):
        try:
            return self.service.create_certificate(data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"签发证书异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="签发证书失败")
