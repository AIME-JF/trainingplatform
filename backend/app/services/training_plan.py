"""
培训计划管理服务
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.training_plan import TrainingPlan
from app.schemas.training_plan import TrainingPlanCreate, TrainingPlanUpdate, TrainingPlanResponse
from app.schemas import PaginatedResponse
from logger import logger


class TrainingPlanService:
    """培训计划服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_list(
        self,
        page: int = 1,
        size: int = 10,
        year: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[TrainingPlanResponse]:
        query = self.db.query(TrainingPlan)

        if year:
            query = query.filter(TrainingPlan.year == year)
        if search:
            query = query.filter(TrainingPlan.name.ilike(f"%{search}%"))

        query = query.order_by(TrainingPlan.created_at.desc())
        total = query.count()

        if size == -1:
            items = query.all()
        else:
            skip = (page - 1) * size
            items = query.offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[TrainingPlanResponse.model_validate(item) for item in items],
        )

    def get_by_id(self, plan_id: int) -> Optional[TrainingPlanResponse]:
        plan = self.db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            return None
        return TrainingPlanResponse.model_validate(plan)

    def create(self, data: TrainingPlanCreate, user_id: int) -> TrainingPlanResponse:
        plan = TrainingPlan(**data.model_dump(), created_by=user_id)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"创建培训计划: {plan.name} (id={plan.id})")
        return TrainingPlanResponse.model_validate(plan)

    def update(self, plan_id: int, data: TrainingPlanUpdate) -> Optional[TrainingPlanResponse]:
        plan = self.db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"更新培训计划: {plan.name} (id={plan.id})")
        return TrainingPlanResponse.model_validate(plan)

    def delete(self, plan_id: int) -> bool:
        plan = self.db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            return False
        self.db.delete(plan)
        self.db.commit()
        logger.info(f"删除培训计划: id={plan_id}")
        return True
