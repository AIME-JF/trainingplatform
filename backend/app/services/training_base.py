"""
培训基地服务
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Department, TrainingBase
from app.schemas import PaginatedResponse
from app.schemas.training import TrainingBaseCreate, TrainingBaseResponse, TrainingBaseUpdate
from app.utils.authz import can_view_training_base, can_view_training_base_with_context
from app.utils.data_scope import build_data_scope_context, can_assign_scoped_values
from logger import logger


class TrainingBaseService:
    """培训基地服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_training_bases(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[TrainingBaseResponse]:
        query = self.db.query(TrainingBase).options(
            joinedload(TrainingBase.department),
            joinedload(TrainingBase.linked_trainings),
        )

        if search:
            query = query.filter(
                or_(TrainingBase.name.contains(search), TrainingBase.location.contains(search))
            )
        if department_id:
            query = query.filter(TrainingBase.department_id == department_id)

        query = query.order_by(TrainingBase.created_at.desc(), TrainingBase.id.desc())
        items = query.all()
        scope_context = build_data_scope_context(self.db, current_user_id) if current_user_id else None
        if scope_context:
            items = [
                item
                for item in items
                if can_view_training_base_with_context(scope_context, item)
            ]
        total = len(items)

        if size != -1:
            skip = (page - 1) * size
            items = items[skip: skip + size]

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_response(item) for item in items],
        )

    def get_training_base_by_id(
        self,
        training_base_id: int,
        current_user_id: Optional[int] = None,
    ) -> Optional[TrainingBaseResponse]:
        training_base = self.db.query(TrainingBase).options(
            joinedload(TrainingBase.department),
            joinedload(TrainingBase.linked_trainings),
        ).filter(TrainingBase.id == training_base_id).first()
        if not training_base:
            return None
        if current_user_id and not can_view_training_base(self.db, training_base, current_user_id):
            return None
        return self._to_response(training_base)

    def create_training_base(self, data: TrainingBaseCreate, user_id: Optional[int] = None) -> TrainingBaseResponse:
        self._ensure_department(data.department_id)
        if user_id:
            self._ensure_actor_can_assign_training_base_scope(user_id, data.department_id)
        training_base = TrainingBase(
            name=data.name,
            location=data.location,
            department_id=data.department_id,
            created_by=user_id,
            description=data.description,
        )
        self.db.add(training_base)
        self.db.commit()
        self.db.refresh(training_base)
        logger.info("创建培训基地: %s", training_base.name)
        return self.get_training_base_by_id(training_base.id)

    def update_training_base(self, training_base_id: int, data: TrainingBaseUpdate) -> Optional[TrainingBaseResponse]:
        training_base = self.db.query(TrainingBase).filter(TrainingBase.id == training_base_id).first()
        if not training_base:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "department_id" in update_data:
            self._ensure_department(update_data["department_id"])

        for field, value in update_data.items():
            setattr(training_base, field, value)

        self.db.commit()
        self.db.refresh(training_base)
        logger.info("更新培训基地: %s", training_base.name)
        return self.get_training_base_by_id(training_base_id)

    def delete_training_base(self, training_base_id: int) -> bool:
        training_base = self.db.query(TrainingBase).options(
            joinedload(TrainingBase.linked_trainings),
        ).filter(TrainingBase.id == training_base_id).first()
        if not training_base:
            return False
        if training_base.linked_trainings:
            raise ValueError("培训基地已被培训班使用，不能删除")

        self.db.delete(training_base)
        self.db.commit()
        logger.info("删除培训基地: %s", training_base_id)
        return True

    def _ensure_department(self, department_id: Optional[int]) -> Optional[Department]:
        if not department_id:
            return None
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("部门不存在")
        return department

    def _ensure_actor_can_assign_training_base_scope(
        self,
        user_id: int,
        department_id: Optional[int],
    ) -> None:
        context = build_data_scope_context(self.db, user_id)
        if not can_assign_scoped_values(
            context,
            department_id=department_id,
            dimension_mode="all",
            treat_missing_as_unrestricted=True,
        ):
            raise ValueError("超出当前角色可操作的数据范围")

    def _to_response(self, training_base: TrainingBase) -> TrainingBaseResponse:
        linked_trainings = training_base.linked_trainings or []
        upcoming_training_count = sum(1 for item in linked_trainings if (item.status or "upcoming") == "upcoming")
        active_training_count = sum(1 for item in linked_trainings if (item.status or "upcoming") == "active")
        return TrainingBaseResponse(
            id=training_base.id,
            name=training_base.name,
            location=training_base.location,
            department_id=training_base.department_id,
            department_name=training_base.department.name if training_base.department else None,
            created_by=training_base.created_by,
            description=training_base.description,
            linked_training_count=len(linked_trainings),
            upcoming_training_count=upcoming_training_count,
            active_training_count=active_training_count,
            created_at=training_base.created_at,
            updated_at=training_base.updated_at,
        )
