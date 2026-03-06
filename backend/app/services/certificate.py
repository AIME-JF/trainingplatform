"""
证书管理服务
"""
from typing import Optional
from datetime import datetime, date
import uuid
from sqlalchemy.orm import Session, joinedload

from app.models import Certificate, User, Training
from app.schemas.certificate import CertificateCreate, CertificateResponse
from app.schemas import PaginatedResponse
from logger import logger


class CertificateService:
    """证书服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_certificates(
        self,
        page: int = 1,
        size: int = 10,
        user_id: Optional[int] = None,
        training_id: Optional[int] = None
    ) -> PaginatedResponse[CertificateResponse]:
        """获取证书列表"""
        query = self.db.query(Certificate).options(
            joinedload(Certificate.user)
        )

        if user_id:
            query = query.filter(Certificate.user_id == user_id)
        if training_id:
            query = query.filter(Certificate.training_id == training_id)

        query = query.order_by(Certificate.created_at.desc())
        total = query.count()

        if size == -1:
            certs = query.all()
        else:
            skip = (page - 1) * size
            certs = query.offset(skip).limit(size).all()

        items = [self._to_response(c) for c in certs]

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def create_certificate(self, data: CertificateCreate) -> CertificateResponse:
        """签发证书"""
        cert_no = f"GXPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        training_name = data.training_name
        if data.training_id and not training_name:
            training = self.db.query(Training).filter(Training.id == data.training_id).first()
            if training:
                training_name = training.name

        cert = Certificate(
            cert_no=cert_no, user_id=data.user_id,
            training_id=data.training_id, training_name=training_name,
            score=data.score,
            issue_date=data.issue_date or date.today(),
            expire_date=data.expire_date
        )
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        logger.info(f"签发证书: {cert_no}")
        return self._to_response(cert)

    def _to_response(self, cert: Certificate) -> CertificateResponse:
        """转换为响应"""
        user = cert.user if hasattr(cert, 'user') and cert.user else None
        return CertificateResponse(
            id=cert.id, cert_no=cert.cert_no,
            user_id=cert.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            training_id=cert.training_id,
            training_name=cert.training_name,
            score=cert.score, issue_date=cert.issue_date,
            expire_date=cert.expire_date,
            created_at=cert.created_at
        )
