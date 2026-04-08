"""
评价模块服务
"""
from typing import List, Optional

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session, joinedload

from app.models.evaluation import (
    VALID_TARGET_TYPES,
    EvaluationDimension,
    EvaluationRecord,
    EvaluationScore,
    EvaluationTask,
    EvaluationTemplate,
)
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationDimensionCreate,
    EvaluationDimensionResponse,
    EvaluationDimensionStat,
    EvaluationDimensionUpdate,
    EvaluationRecordResponse,
    EvaluationScoreResponse,
    EvaluationSubmit,
    EvaluationSummaryResponse,
    EvaluationTaskCreate,
    EvaluationTaskResponse,
    EvaluationTaskUpdate,
    EvaluationTemplateResponse,
    EvaluationTemplateUpdate,
)
from logger import logger


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db

    # ========== 模板 ==========

    def list_templates(self, target_type: Optional[str] = None) -> List[EvaluationTemplateResponse]:
        query = self.db.query(EvaluationTemplate).options(
            joinedload(EvaluationTemplate.dimensions),
        )
        if target_type:
            query = query.filter(EvaluationTemplate.target_type == target_type)
        templates = query.order_by(EvaluationTemplate.id).all()
        return [EvaluationTemplateResponse.model_validate(t) for t in templates]

    def get_template(self, template_id: int) -> Optional[EvaluationTemplateResponse]:
        t = self.db.query(EvaluationTemplate).options(
            joinedload(EvaluationTemplate.dimensions),
        ).filter(EvaluationTemplate.id == template_id).first()
        if not t:
            return None
        return EvaluationTemplateResponse.model_validate(t)

    def get_template_by_target_type(self, target_type: str) -> Optional[EvaluationTemplate]:
        return self.db.query(EvaluationTemplate).filter(
            EvaluationTemplate.target_type == target_type,
        ).first()

    def update_template(self, template_id: int, data: EvaluationTemplateUpdate) -> EvaluationTemplateResponse:
        t = self.db.query(EvaluationTemplate).filter(EvaluationTemplate.id == template_id).first()
        if not t:
            raise ValueError("模板不存在")
        if data.name is not None:
            t.name = data.name
        if data.description is not None:
            t.description = data.description
        if data.enabled is not None:
            t.enabled = data.enabled
        self.db.commit()
        self.db.refresh(t)
        return self.get_template(template_id)

    # ========== 维度 ==========

    def add_dimension(self, template_id: int, data: EvaluationDimensionCreate) -> EvaluationDimensionResponse:
        t = self.db.query(EvaluationTemplate).filter(EvaluationTemplate.id == template_id).first()
        if not t:
            raise ValueError("模板不存在")
        dim = EvaluationDimension(
            template_id=template_id,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
            weight=data.weight,
        )
        self.db.add(dim)
        self.db.commit()
        self.db.refresh(dim)
        return EvaluationDimensionResponse.model_validate(dim)

    def update_dimension(self, dimension_id: int, data: EvaluationDimensionUpdate) -> EvaluationDimensionResponse:
        dim = self.db.query(EvaluationDimension).filter(EvaluationDimension.id == dimension_id).first()
        if not dim:
            raise ValueError("维度不存在")
        if data.name is not None:
            dim.name = data.name
        if data.description is not None:
            dim.description = data.description
        if data.sort_order is not None:
            dim.sort_order = data.sort_order
        if data.weight is not None:
            dim.weight = data.weight
        self.db.commit()
        self.db.refresh(dim)
        return EvaluationDimensionResponse.model_validate(dim)

    def delete_dimension(self, dimension_id: int) -> None:
        dim = self.db.query(EvaluationDimension).filter(EvaluationDimension.id == dimension_id).first()
        if not dim:
            raise ValueError("维度不存在")
        self.db.delete(dim)
        self.db.commit()

    # ========== 任务 ==========

    def create_task(self, data: EvaluationTaskCreate, created_by: int) -> EvaluationTaskResponse:
        if data.target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"无效的评价对象类型: {data.target_type}")
        template = self.get_template_by_target_type(data.target_type)
        if not template:
            raise ValueError(f"未找到 {data.target_type} 类型的评价模板")
        if not template.enabled:
            raise ValueError("该评价模板已停用")

        task = EvaluationTask(
            template_id=template.id,
            target_type=data.target_type,
            target_id=data.target_id,
            training_id=data.training_id,
            title=data.title,
            status=data.status,
            start_time=data.start_time,
            end_time=data.end_time,
            source="manual",
            created_by=created_by,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info("创建评价任务: %s", task.title)
        return self._task_to_response(task)

    def list_tasks(self, target_type: Optional[str] = None, status: Optional[str] = None) -> List[EvaluationTaskResponse]:
        query = self.db.query(EvaluationTask)
        if target_type:
            query = query.filter(EvaluationTask.target_type == target_type)
        if status:
            query = query.filter(EvaluationTask.status == status)
        tasks = query.order_by(EvaluationTask.created_at.desc()).all()
        return [self._task_to_response(t) for t in tasks]

    def update_task(self, task_id: int, data: EvaluationTaskUpdate) -> EvaluationTaskResponse:
        task = self.db.query(EvaluationTask).filter(EvaluationTask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        if data.title is not None:
            task.title = data.title
        if data.status is not None:
            task.status = data.status
        if data.start_time is not None:
            task.start_time = data.start_time
        if data.end_time is not None:
            task.end_time = data.end_time
        self.db.commit()
        self.db.refresh(task)
        return self._task_to_response(task)

    def delete_task(self, task_id: int) -> None:
        task = self.db.query(EvaluationTask).filter(EvaluationTask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        self.db.delete(task)
        self.db.commit()

    # ========== 评价提交 ==========

    def submit_evaluation(self, user_id: int, data: EvaluationSubmit) -> EvaluationRecordResponse:
        if data.target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"无效的评价对象类型: {data.target_type}")
        template = self.get_template_by_target_type(data.target_type)
        if not template:
            raise ValueError(f"未找到 {data.target_type} 类型的评价模板")
        if not template.enabled:
            raise ValueError("该评价模板已停用")

        training_id = data.training_id
        # 检查是否已评价
        existing = self.db.query(EvaluationRecord).filter(
            EvaluationRecord.template_id == template.id,
            EvaluationRecord.target_id == data.target_id,
            EvaluationRecord.user_id == user_id,
            EvaluationRecord.training_id == training_id,
        ).first()
        if existing:
            raise ValueError("您已对该对象提交过评价")

        # 计算均分
        total_score = sum(s.score for s in data.scores)
        avg_score = round(total_score / len(data.scores), 2) if data.scores else 0

        record = EvaluationRecord(
            template_id=template.id,
            task_id=data.task_id,
            target_type=data.target_type,
            target_id=data.target_id,
            user_id=user_id,
            training_id=training_id,
            comment=data.comment,
            avg_score=avg_score,
        )
        self.db.add(record)
        self.db.flush()

        for item in data.scores:
            self.db.add(EvaluationScore(
                record_id=record.id,
                dimension_id=item.dimension_id,
                score=item.score,
            ))

        self.db.commit()
        self.db.refresh(record)
        logger.info("提交评价: target=%s/%s, user=%s", data.target_type, data.target_id, user_id)
        return self._record_to_response(record)

    # ========== 记录查询 ==========

    def list_records(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        user_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> List[EvaluationRecordResponse]:
        query = self.db.query(EvaluationRecord).options(
            joinedload(EvaluationRecord.scores).joinedload(EvaluationScore.dimension),
            joinedload(EvaluationRecord.user),
        )
        if target_type:
            query = query.filter(EvaluationRecord.target_type == target_type)
        if target_id:
            query = query.filter(EvaluationRecord.target_id == target_id)
        if user_id:
            query = query.filter(EvaluationRecord.user_id == user_id)
        if task_id:
            query = query.filter(EvaluationRecord.task_id == task_id)
        records = query.order_by(EvaluationRecord.created_at.desc()).all()
        return [self._record_to_response(r) for r in records]

    def get_summary(self, target_type: str, target_id: int) -> EvaluationSummaryResponse:
        """获取某对象的评价统计"""
        template = self.get_template_by_target_type(target_type)
        if not template:
            return EvaluationSummaryResponse(target_type=target_type, target_id=target_id)

        records = self.db.query(EvaluationRecord).filter(
            EvaluationRecord.target_type == target_type,
            EvaluationRecord.target_id == target_id,
        ).all()
        total_count = len(records)
        if not total_count:
            return EvaluationSummaryResponse(target_type=target_type, target_id=target_id)

        overall_avg = round(sum(r.avg_score for r in records) / total_count, 2)
        record_ids = [r.id for r in records]

        # 各维度统计
        dim_stats = self.db.query(
            EvaluationScore.dimension_id,
            sa_func.avg(EvaluationScore.score).label("avg_score"),
            sa_func.count(EvaluationScore.id).label("count"),
        ).filter(
            EvaluationScore.record_id.in_(record_ids),
        ).group_by(EvaluationScore.dimension_id).all()

        dim_map = {}
        for dim in (template.dimensions or []):
            dim_map[dim.id] = dim.name

        dimensions = []
        for stat in dim_stats:
            dimensions.append(EvaluationDimensionStat(
                dimension_id=stat.dimension_id,
                dimension_name=dim_map.get(stat.dimension_id, f"维度#{stat.dimension_id}"),
                avg_score=round(float(stat.avg_score), 2),
                count=stat.count,
            ))

        return EvaluationSummaryResponse(
            target_type=target_type,
            target_id=target_id,
            total_count=total_count,
            overall_avg=overall_avg,
            dimensions=dimensions,
        )

    # ========== 内部方法 ==========

    def _task_to_response(self, task: EvaluationTask) -> EvaluationTaskResponse:
        record_count = self.db.query(sa_func.count(EvaluationRecord.id)).filter(
            EvaluationRecord.task_id == task.id,
        ).scalar() or 0
        return EvaluationTaskResponse(
            id=task.id,
            template_id=task.template_id,
            target_type=task.target_type,
            target_id=task.target_id,
            training_id=task.training_id,
            title=task.title,
            status=task.status,
            source=task.source or "manual",
            start_time=task.start_time,
            end_time=task.end_time,
            created_by=task.created_by,
            created_at=task.created_at,
            record_count=record_count,
        )

    def _record_to_response(self, record: EvaluationRecord) -> EvaluationRecordResponse:
        user = record.user if getattr(record, "user", None) else self.db.query(User).filter(User.id == record.user_id).first()
        scores = []
        for s in (record.scores or []):
            dim_name = s.dimension.name if getattr(s, "dimension", None) else None
            scores.append(EvaluationScoreResponse(
                id=s.id,
                dimension_id=s.dimension_id,
                dimension_name=dim_name,
                score=s.score,
            ))
        return EvaluationRecordResponse(
            id=record.id,
            template_id=record.template_id,
            task_id=record.task_id,
            target_type=record.target_type,
            target_id=record.target_id,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            training_id=record.training_id,
            comment=record.comment,
            avg_score=record.avg_score or 0,
            scores=scores,
            created_at=record.created_at,
        )
