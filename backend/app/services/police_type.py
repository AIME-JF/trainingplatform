"""
警种管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import PoliceType
from app.schemas.police_type import (
    PoliceTypeCreate, PoliceTypeUpdate, PoliceTypeSimpleResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class PoliceTypeService:
    """警种服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_police_type(self, data: PoliceTypeCreate) -> PoliceTypeSimpleResponse:
        """创建警种"""
        if self.db.query(PoliceType).filter(PoliceType.code == data.code).first():
            raise ValueError("警种编码已存在")
        if self.db.query(PoliceType).filter(PoliceType.name == data.name).first():
            raise ValueError("警种名称已存在")

        db_obj = PoliceType(
            name=data.name,
            code=data.code,
            description=data.description,
            is_active=True
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        logger.info(f"创建警种成功: {data.code}")
        return PoliceTypeSimpleResponse.model_validate(db_obj)

    def get_police_type_by_id(self, police_type_id: int) -> Optional[PoliceTypeSimpleResponse]:
        """根据ID获取警种"""
        obj = self.db.query(PoliceType).filter(PoliceType.id == police_type_id).first()
        if not obj:
            return None
        return PoliceTypeSimpleResponse.model_validate(obj)

    def get_police_types(
        self,
        page: int = 1,
        size: int = 10,
        name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> PaginatedResponse[PoliceTypeSimpleResponse]:
        """获取警种列表"""
        query = self.db.query(PoliceType)

        if name:
            query = query.filter(PoliceType.name.contains(name))
        if is_active is not None:
            query = query.filter(PoliceType.is_active == is_active)

        query = query.order_by(PoliceType.id.asc())

        if size == -1:
            items = query.all()
            total = len(items)
            return PaginatedResponse(
                page=1, size=total, total=total,
                items=[PoliceTypeSimpleResponse.model_validate(i) for i in items]
            )

        total = self.db.query(func.count(PoliceType.id)).scalar()
        skip = (page - 1) * size
        items = query.offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page, size=size, total=total,
            items=[PoliceTypeSimpleResponse.model_validate(i) for i in items]
        )

    def update_police_type(self, police_type_id: int, data: PoliceTypeUpdate) -> Optional[PoliceTypeSimpleResponse]:
        """更新警种"""
        obj = self.db.query(PoliceType).filter(PoliceType.id == police_type_id).first()
        if not obj:
            return None

        if data.name and data.name != obj.name:
            if self.db.query(PoliceType).filter(PoliceType.name == data.name, PoliceType.id != police_type_id).first():
                raise ValueError("警种名称已存在")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)

        self.db.commit()
        self.db.refresh(obj)

        logger.info(f"更新警种成功: {obj.code}")
        return PoliceTypeSimpleResponse.model_validate(obj)

    def delete_police_type(self, police_type_id: int) -> bool:
        """删除警种"""
        obj = self.db.query(PoliceType).filter(PoliceType.id == police_type_id).first()
        if not obj:
            return False

        if obj.users:
            raise ValueError("不能删除有关联用户的警种")

        self.db.delete(obj)
        self.db.commit()

        logger.info(f"删除警种成功: {obj.code}")
        return True
