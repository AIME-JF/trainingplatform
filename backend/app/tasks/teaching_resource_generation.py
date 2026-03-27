"""
教学资源生成 Celery 任务。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal, get_redis
from app.models import AITask
from app.services.teaching_resource_generation import TeachingResourceGenerationService
from celery_app import celery_app
from logger import logger


RESOURCE_GENERATION_TASK_TYPE = "resource_generation"
RESOURCE_GENERATION_DISPATCH_LOCK = "teaching-resource-generation:dispatch-lock"
TEACHING_RESOURCE_GENERATION_TASK_NAME = "app.tasks.teaching_resource_generation.generate_teaching_resource_generation_task"
LEGACY_AI_RESOURCE_GENERATION_TASK_NAME = "app.tasks.ai_resource_generation.generate_ai_resource_generation_task"


def _run_teaching_resource_generation_task(task_self, task_id: int) -> None:
    db = SessionLocal()
    should_schedule_next = False

    try:
        task = db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == RESOURCE_GENERATION_TASK_TYPE,
        ).first()
        if not task:
            logger.warning("教学资源生成任务不存在: %s", task_id)
            return

        if task.status in {"completed", "confirmed", "failed"}:
            logger.info("教学资源生成任务已结束，跳过重复执行: %s", task_id)
            return

        TeachingResourceGenerationService(db).execute_task(task_id)
        should_schedule_next = True
        logger.info("教学资源生成任务完成: %s", task_id)
    except Exception as exc:
        db.rollback()
        logger.error("教学资源生成任务执行失败(task_id=%s, retry=%s): %s", task_id, task_self.request.retries, exc)

        if task_self.request.retries < task_self.max_retries:
            raise task_self.retry(exc=exc, countdown=3 * (task_self.request.retries + 1))

        TeachingResourceGenerationService(db).mark_task_failed(task_id, str(exc))
        should_schedule_next = True
    finally:
        db.close()

    if should_schedule_next:
        try:
            schedule_teaching_resource_generation_task()
        except Exception as exc:
            logger.error("教学资源生成任务后续调度失败: %s", exc)


@celery_app.task(bind=True, name=TEACHING_RESOURCE_GENERATION_TASK_NAME, max_retries=3)
def generate_teaching_resource_generation_task(self, task_id: int) -> None:
    """执行教学资源生成任务"""
    _run_teaching_resource_generation_task(self, task_id)


@celery_app.task(bind=True, name=LEGACY_AI_RESOURCE_GENERATION_TASK_NAME, max_retries=3)
def generate_ai_resource_generation_task(self, task_id: int) -> None:
    """兼容旧任务名的教学资源生成任务"""
    _run_teaching_resource_generation_task(self, task_id)


def schedule_teaching_resource_generation_task(preferred_task_id: Optional[int] = None, db: Optional[Session] = None) -> Optional[int]:
    """调度下一个教学资源生成任务"""
    lock = None
    own_session = db is None
    session = db or SessionLocal()

    try:
        lock = _acquire_dispatch_lock()
        if session.query(AITask.id).filter(
            AITask.task_type == RESOURCE_GENERATION_TASK_TYPE,
            AITask.status == "processing",
        ).first():
            return None

        next_task = _pick_next_pending_task(session, preferred_task_id)
        if not next_task:
            return None

        next_task.status = "processing"
        next_task.started_at = next_task.started_at or datetime.now()
        next_task.completed_at = None
        next_task.error_message = None
        session.commit()

        try:
            generate_teaching_resource_generation_task.apply_async(
                args=[next_task.id],
                task_id=f"teaching-resource-generation-task-{next_task.id}",
            )
        except Exception as exc:
            session.rollback()
            revert_task = session.query(AITask).filter(AITask.id == next_task.id).first()
            if revert_task:
                revert_task.status = "pending"
                revert_task.started_at = None
                revert_task.completed_at = None
                revert_task.error_message = f"任务调度失败: {exc}"
                session.commit()
            logger.error("调度教学资源生成任务失败: %s", exc)
            return None

        logger.info("教学资源生成任务已加入 Celery: %s", next_task.id)
        return next_task.id
    finally:
        if lock is not None:
            try:
                lock.release()
            except Exception:
                pass
        if own_session:
            session.close()


def _pick_next_pending_task(session: Session, preferred_task_id: Optional[int]) -> Optional[AITask]:
    if preferred_task_id:
        task = session.query(AITask).filter(
            AITask.id == preferred_task_id,
            AITask.task_type == RESOURCE_GENERATION_TASK_TYPE,
            AITask.status == "pending",
        ).with_for_update().first()
        if task:
            return task

    return session.query(AITask).filter(
        AITask.task_type == RESOURCE_GENERATION_TASK_TYPE,
        AITask.status == "pending",
    ).order_by(AITask.created_at.asc(), AITask.id.asc()).with_for_update().first()


def _acquire_dispatch_lock():
    try:
        redis_client = get_redis()
        lock = redis_client.lock(RESOURCE_GENERATION_DISPATCH_LOCK, timeout=30, blocking_timeout=5)
        if not lock.acquire(blocking=True):
            logger.warning("获取教学资源生成调度锁失败")
            return None
        return lock
    except Exception as exc:
        logger.warning("获取教学资源生成调度锁异常，改为无锁调度: %s", exc)
        return None
