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
    EvaluationTaskItem,
    EvaluationTemplate,
)
from app.models.training import Training, TrainingCourse, Enrollment
from app.models.user import User
from app.models.notice import Notice
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
    EvaluationTaskDetailResponse,
    EvaluationTaskItemResponse,
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
        return self.db.query(EvaluationTemplate).options(
            joinedload(EvaluationTemplate.dimensions),
        ).filter(
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
            template_id=template_id, name=data.name, description=data.description,
            sort_order=data.sort_order, weight=data.weight,
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

    def create_training_evaluation_task(self, training_id: int, title: str, source: str = "manual",
                                         created_by: Optional[int] = None, start_time=None, end_time=None) -> EvaluationTaskResponse:
        """为培训班创建评价任务，自动生成评价项清单"""
        training = self.db.query(Training).options(
            joinedload(Training.courses).joinedload(TrainingCourse.primary_instructor),
            joinedload(Training.training_base),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        # 获取培训班模板
        training_template = self.get_template_by_target_type("training")
        if not training_template:
            raise ValueError("培训班评价模板不存在")

        task = EvaluationTask(
            template_id=training_template.id,
            target_type="training",
            target_id=training_id,
            training_id=training_id,
            title=title,
            status="active",
            source=source,
            start_time=start_time,
            end_time=end_time,
            created_by=created_by,
        )
        self.db.add(task)
        self.db.flush()

        # 生成评价项清单
        sort_order = 0
        seen_instructors = set()

        for course in (training.courses or []):
            # 课程评价项
            sort_order += 1
            self.db.add(EvaluationTaskItem(
                task_id=task.id, target_type="course", target_id=course.id,
                target_name=course.name, sort_order=sort_order,
            ))
            # 主讲教官评价项
            if course.primary_instructor_id and course.primary_instructor_id not in seen_instructors:
                sort_order += 1
                instructor_name = None
                if course.primary_instructor:
                    instructor_name = course.primary_instructor.nickname or course.primary_instructor.username
                elif course.instructor:
                    instructor_name = course.instructor
                self.db.add(EvaluationTaskItem(
                    task_id=task.id, target_type="instructor", target_id=course.primary_instructor_id,
                    target_name=instructor_name, sort_order=sort_order,
                ))
                seen_instructors.add(course.primary_instructor_id)

        # 培训班评价项
        sort_order += 1
        self.db.add(EvaluationTaskItem(
            task_id=task.id, target_type="training", target_id=training_id,
            target_name=training.name, sort_order=sort_order,
        ))

        # 培训基地评价项（如果有）
        if training.training_base_id and training.training_base:
            sort_order += 1
            self.db.add(EvaluationTaskItem(
                task_id=task.id, target_type="training_base", target_id=training.training_base_id,
                target_name=training.training_base.name, sort_order=sort_order,
            ))

        self.db.commit()
        self.db.refresh(task)
        logger.info("创建培训班评价任务: training_id=%s, task_id=%s", training_id, task.id)
        return self._task_to_response(task)

    def create_task(self, data: EvaluationTaskCreate, created_by: int) -> EvaluationTaskResponse:
        """手动创建评价任务（统一走培训班维度）"""
        return self.create_training_evaluation_task(
            training_id=data.training_id,
            title=data.title,
            source="manual",
            created_by=created_by,
            start_time=data.start_time,
            end_time=data.end_time,
        )

    def list_tasks(self, target_type: Optional[str] = None, status: Optional[str] = None,
                   current_user_id: Optional[int] = None) -> List[EvaluationTaskResponse]:
        query = self.db.query(EvaluationTask)
        if target_type:
            query = query.filter(EvaluationTask.target_type == target_type)
        if status:
            query = query.filter(EvaluationTask.status == status)
        tasks = query.order_by(EvaluationTask.created_at.desc()).all()
        return [self._task_to_response(t, current_user_id) for t in tasks]

    def get_task_detail(self, task_id: int, user_id: Optional[int] = None) -> Optional[EvaluationTaskDetailResponse]:
        """获取任务详情（含评价项清单和维度）"""
        task = self.db.query(EvaluationTask).options(
            joinedload(EvaluationTask.items),
        ).filter(EvaluationTask.id == task_id).first()
        if not task:
            return None

        # 加载模板和维度
        template_map = {}
        for tpl in self.db.query(EvaluationTemplate).options(joinedload(EvaluationTemplate.dimensions)).all():
            template_map[tpl.target_type] = tpl

        # 检查当前用户哪些项已填写
        completed_keys = set()
        if user_id:
            records = self.db.query(EvaluationRecord).filter(
                EvaluationRecord.task_id == task_id,
                EvaluationRecord.user_id == user_id,
            ).all()
            for r in records:
                completed_keys.add(f"{r.target_type}:{r.target_id}")

        items = []
        for item in (task.items or []):
            tpl = template_map.get(item.target_type)
            dims = [EvaluationDimensionResponse.model_validate(d) for d in (tpl.dimensions if tpl else [])]
            items.append(EvaluationTaskItemResponse(
                id=item.id, task_id=item.task_id, target_type=item.target_type,
                target_id=item.target_id, target_name=item.target_name,
                sort_order=item.sort_order, dimensions=dims,
                completed=f"{item.target_type}:{item.target_id}" in completed_keys,
            ))

        training = self.db.query(Training).filter(Training.id == task.training_id).first() if task.training_id else None
        all_completed = bool(items) and all(i.completed for i in items)

        return EvaluationTaskDetailResponse(
            id=task.id, title=task.title, training_id=task.training_id,
            training_name=training.name if training else None,
            status=task.status, items=items, completed=all_completed,
        )

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

    def submit_evaluation(self, user_id: int, data: EvaluationSubmit) -> List[EvaluationRecordResponse]:
        """批量提交评价（一个任务的所有评价项一次提交）"""
        task = self.db.query(EvaluationTask).filter(EvaluationTask.id == data.task_id).first()
        if not task:
            raise ValueError("评价任务不存在")
        if task.status != "active":
            raise ValueError("该评价任务已结束")

        results = []
        for submit_item in data.items:
            if submit_item.target_type not in VALID_TARGET_TYPES:
                raise ValueError(f"无效的评价对象类型: {submit_item.target_type}")

            template = self.get_template_by_target_type(submit_item.target_type)
            if not template:
                raise ValueError(f"未找到 {submit_item.target_type} 类型的评价模板")

            # 检查是否已评价
            existing = self.db.query(EvaluationRecord).filter(
                EvaluationRecord.task_id == data.task_id,
                EvaluationRecord.target_type == submit_item.target_type,
                EvaluationRecord.target_id == submit_item.target_id,
                EvaluationRecord.user_id == user_id,
            ).first()
            if existing:
                continue  # 跳过已评价的项

            total_score = sum(s.score for s in submit_item.scores)
            avg_score = round(total_score / len(submit_item.scores), 2) if submit_item.scores else 0

            record = EvaluationRecord(
                template_id=template.id,
                task_id=data.task_id,
                target_type=submit_item.target_type,
                target_id=submit_item.target_id,
                user_id=user_id,
                training_id=task.training_id,
                comment=submit_item.comment,
                avg_score=avg_score,
            )
            self.db.add(record)
            self.db.flush()

            for score_item in submit_item.scores:
                self.db.add(EvaluationScore(
                    record_id=record.id,
                    dimension_id=score_item.dimension_id,
                    score=score_item.score,
                ))

            results.append(record)

        self.db.commit()
        for r in results:
            self.db.refresh(r)

        logger.info("批量提交评价: task_id=%s, user=%s, %d项", data.task_id, user_id, len(results))
        return [self._record_to_response(r) for r in results]

    # ========== 记录查询 ==========

    def list_records(self, target_type=None, target_id=None, user_id=None, task_id=None) -> List[EvaluationRecordResponse]:
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

        dim_stats = self.db.query(
            EvaluationScore.dimension_id,
            sa_func.avg(EvaluationScore.score).label("avg_score"),
            sa_func.count(EvaluationScore.id).label("count"),
        ).filter(
            EvaluationScore.record_id.in_(record_ids),
        ).group_by(EvaluationScore.dimension_id).all()

        dim_map = {d.id: d.name for d in (template.dimensions or [])}
        dimensions = [
            EvaluationDimensionStat(
                dimension_id=s.dimension_id,
                dimension_name=dim_map.get(s.dimension_id, f"维度#{s.dimension_id}"),
                avg_score=round(float(s.avg_score), 2), count=s.count,
            ) for s in dim_stats
        ]

        return EvaluationSummaryResponse(
            target_type=target_type, target_id=target_id,
            total_count=total_count, overall_avg=overall_avg, dimensions=dimensions,
        )

    # ========== 结班自动触发 ==========

    def trigger_training_evaluation(self, training_id: int) -> Optional[int]:
        """结班时自动创建评价任务并通知学员"""
        training = self.db.query(Training).options(
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return None

        # 检查是否已有该培训班的评价任务
        existing = self.db.query(EvaluationTask).filter(
            EvaluationTask.training_id == training_id,
            EvaluationTask.source == "auto",
        ).first()
        if existing:
            logger.info("培训班 %s 已有自动评价任务，跳过", training_id)
            return existing.id

        task_resp = self.create_training_evaluation_task(
            training_id=training_id,
            title=f"{training.name} - 结班评价",
            source="auto",
        )

        # 给所有已批准学员发送通知
        approved_enrollments = [e for e in (training.enrollments or []) if e.status == "approved"]
        for enrollment in approved_enrollments:
            notice = Notice(
                title="请完成培训评价",
                content=f"培训班「{training.name}」已结班，请尽快完成评价问卷。",
                type="reminder",
                training_id=training_id,
                target_user_id=enrollment.user_id,
                reminder_type="evaluation_pending",
            )
            self.db.add(notice)
        self.db.commit()

        logger.info("结班自动创建评价任务: training_id=%s, task_id=%s, 通知%d名学员",
                     training_id, task_resp.id, len(approved_enrollments))
        return task_resp.id

    # ========== 内部方法 ==========

    def _task_to_response(self, task: EvaluationTask, current_user_id: Optional[int] = None) -> EvaluationTaskResponse:
        record_count = self.db.query(sa_func.count(EvaluationRecord.id)).filter(
            EvaluationRecord.task_id == task.id,
        ).scalar() or 0
        item_count = self.db.query(sa_func.count(EvaluationTaskItem.id)).filter(
            EvaluationTaskItem.task_id == task.id,
        ).scalar() or 0
        user_completed = False
        if current_user_id and item_count > 0:
            user_record_count = self.db.query(sa_func.count(EvaluationRecord.id)).filter(
                EvaluationRecord.task_id == task.id,
                EvaluationRecord.user_id == current_user_id,
            ).scalar() or 0
            user_completed = user_record_count >= item_count
        training = self.db.query(Training).filter(Training.id == task.training_id).first() if task.training_id else None
        return EvaluationTaskResponse(
            id=task.id, template_id=task.template_id, target_type=task.target_type,
            target_id=task.target_id, training_id=task.training_id,
            training_name=training.name if training else None,
            title=task.title, status=task.status, source=task.source or "manual",
            start_time=task.start_time, end_time=task.end_time,
            created_by=task.created_by, created_at=task.created_at,
            record_count=record_count, item_count=item_count,
            user_completed=user_completed,
        )

    def _record_to_response(self, record: EvaluationRecord) -> EvaluationRecordResponse:
        user = record.user if getattr(record, "user", None) else self.db.query(User).filter(User.id == record.user_id).first()
        scores = []
        for s in (record.scores or []):
            dim_name = s.dimension.name if getattr(s, "dimension", None) else None
            scores.append(EvaluationScoreResponse(
                id=s.id, dimension_id=s.dimension_id, dimension_name=dim_name, score=s.score,
            ))
        return EvaluationRecordResponse(
            id=record.id, template_id=record.template_id, task_id=record.task_id,
            target_type=record.target_type, target_id=record.target_id,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            training_id=record.training_id, comment=record.comment,
            avg_score=record.avg_score or 0, scores=scores, created_at=record.created_at,
        )
