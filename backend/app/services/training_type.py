"""
培训班类型管理服务
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Training
from app.models.training_type import TrainingType
from app.schemas.training_type import (
    TrainingTypeCreate, TrainingTypeUpdate, TrainingTypeResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class TrainingTypeService:
    """培训班类型服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_training_type(self, data: TrainingTypeCreate) -> TrainingTypeResponse:
        """创建培训班类型"""
        if self.db.query(TrainingType).filter(TrainingType.code == data.code).first():
            raise ValueError("类型编码已存在")
        if self.db.query(TrainingType).filter(TrainingType.name == data.name).first():
            raise ValueError("类型名称已存在")

        db_obj = TrainingType(
            name=data.name,
            code=data.code,
            description=data.description,
            is_active=True
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        logger.info(f"创建培训班类型成功: {data.code}")
        return TrainingTypeResponse.model_validate(db_obj)

    def get_training_type_by_id(self, training_type_id: int) -> Optional[TrainingTypeResponse]:
        """根据ID获取培训班类型"""
        obj = self.db.query(TrainingType).filter(TrainingType.id == training_type_id).first()
        if not obj:
            return None
        return TrainingTypeResponse.model_validate(obj)

    def get_training_types(
        self,
        page: int = 1,
        size: int = 10,
        name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> PaginatedResponse[TrainingTypeResponse]:
        """获取培训班类型列表"""
        query = self.db.query(TrainingType)

        if name:
            query = query.filter(TrainingType.name.contains(name))
        if is_active is not None:
            query = query.filter(TrainingType.is_active == is_active)

        query = query.order_by(TrainingType.sort_order.asc(), TrainingType.id.asc())

        if size == -1:
            items = query.all()
            total = len(items)
            return PaginatedResponse(
                page=1, size=total, total=total,
                items=[TrainingTypeResponse.model_validate(i) for i in items]
            )

        total = query.count()
        skip = (page - 1) * size
        items = query.offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page, size=size, total=total,
            items=[TrainingTypeResponse.model_validate(i) for i in items]
        )

    def update_training_type(self, training_type_id: int, data: TrainingTypeUpdate) -> Optional[TrainingTypeResponse]:
        """更新培训班类型"""
        obj = self.db.query(TrainingType).filter(TrainingType.id == training_type_id).first()
        if not obj:
            return None

        if data.name and data.name != obj.name:
            if self.db.query(TrainingType).filter(TrainingType.name == data.name, TrainingType.id != training_type_id).first():
                raise ValueError("类型名称已存在")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)

        self.db.commit()
        self.db.refresh(obj)

        logger.info(f"更新培训班类型成功: {obj.code}")
        return TrainingTypeResponse.model_validate(obj)

    def delete_training_type(self, training_type_id: int) -> bool:
        """删除培训班类型"""
        obj = self.db.query(TrainingType).filter(TrainingType.id == training_type_id).first()
        if not obj:
            return False

        ref_count = self.db.query(func.count(Training.id)).filter(
            Training.training_type_id == training_type_id
        ).scalar()
        if ref_count and ref_count > 0:
            raise ValueError("不能删除有关联培训班的类型")

        self.db.delete(obj)
        self.db.commit()

        logger.info(f"删除培训班类型成功: {obj.code}")
        return True
