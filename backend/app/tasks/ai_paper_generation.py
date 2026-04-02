"""
AI 自动生成试卷/文档生成试卷 Celery 任务。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal, get_redis
from app.models import AITask
from app.services.ai import AIService
from celery_app import celery_app
from logger import logger


PAPER_GENERATION_TASK_TYPE = "paper_generation"
PAPER_DOCUMENT_GENERATION_TASK_TYPE = "paper_document_generation"
PAPER_GENERATION_TASK_TYPES = {
    PAPER_GENERATION_TASK_TYPE,
    PAPER_DOCUMENT_GENERATION_TASK_TYPE,
}
PAPER_GENERATION_DISPATCH_LOCK = "ai:paper-generation:dispatch-lock"
AI_PAPER_GENERATION_TASK_NAME = "app.tasks.ai_paper_generation.generate_ai_paper_generation_task"
PROCESSING_STALE_TIMEOUT_SECONDS = 10 * 60


@celery_app.task(bind=True, name=AI_PAPER_GENERATION_TASK_NAME, max_retries=3)
def generate_ai_paper_generation_task(self, task_id: int, task_type: str) -> None:
    """执行 AI 自动生成试卷类任务"""
    db = SessionLocal()
    should_schedule_next = False

    try:
        task = db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == task_type,
        ).first()
        if not task:
            logger.warning("AI 自动生成试卷类任务不存在: {} ({})", task_id, task_type)
            return

        if task.status in {"completed", "confirmed", "failed"}:
            logger.info("AI 自动生成试卷类任务已结束，跳过重复执行: {} ({})", task_id, task_type)
            return

        service = AIService(db)
        if task_type == PAPER_GENERATION_TASK_TYPE:
            service.execute_paper_generation_task(task_id)
        elif task_type == PAPER_DOCUMENT_GENERATION_TASK_TYPE:
            service.execute_paper_document_generation_task(task_id)
        else:
            raise ValueError(f"不支持的任务类型: {task_type}")

        should_schedule_next = True
        logger.info("AI 自动生成试卷类任务完成: {} ({})", task_id, task_type)
    except Exception as exc:
        db.rollback()
        logger.error(
            "AI 自动生成试卷类任务执行失败(task_id={}, task_type={}, retry={}): {}",
            task_id,
            task_type,
            self.request.retries,
            exc,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=3 * (self.request.retries + 1))

        _mark_task_failed(db, task_id, task_type, str(exc))
        should_schedule_next = True
    finally:
        db.close()

    if should_schedule_next:
        try:
            schedule_ai_paper_generation_task()
        except Exception as exc:
            logger.error("AI 自动生成试卷类任务后续调度失败: {}", exc)


def schedule_ai_paper_generation_task(
    preferred_task_id: Optional[int] = None,
    preferred_task_type: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[int]:
    """调度下一个 AI 自动生成试卷类任务"""
    lock = None
    own_session = db is None
    session = db or SessionLocal()

    try:
        lock = _acquire_dispatch_lock()
        _recover_stale_processing_tasks(session)
        if session.query(AITask.id).filter(
            AITask.task_type.in_(tuple(PAPER_GENERATION_TASK_TYPES)),
            AITask.status == "processing",
        ).first():
            return None

        next_task = _pick_next_pending_task(session, preferred_task_id, preferred_task_type)
        if not next_task:
            return None

        next_task.status = "processing"
        next_task.started_at = next_task.started_at or datetime.now()
        next_task.completed_at = None
        next_task.error_message = None
        session.commit()

        try:
            generate_ai_paper_generation_task.apply_async(
                args=[next_task.id, next_task.task_type],
                task_id=f"ai-paper-generation-task-{next_task.id}",
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
            logger.error("调度 AI 自动生成试卷类任务失败: {}", exc)
            return None

        logger.info("AI 自动生成试卷类任务已加入 Celery: {} ({})", next_task.id, next_task.task_type)
        return next_task.id
    finally:
        if lock is not None:
            try:
                lock.release()
            except Exception:
                pass
        if own_session:
            session.close()


def _pick_next_pending_task(
    session: Session,
    preferred_task_id: Optional[int],
    preferred_task_type: Optional[str],
) -> Optional[AITask]:
    if preferred_task_id and preferred_task_type in PAPER_GENERATION_TASK_TYPES:
        task = session.query(AITask).filter(
            AITask.id == preferred_task_id,
            AITask.task_type == preferred_task_type,
            AITask.status == "pending",
        ).with_for_update().first()
        if task:
            return task

    return session.query(AITask).filter(
        AITask.task_type.in_(tuple(PAPER_GENERATION_TASK_TYPES)),
        AITask.status == "pending",
    ).order_by(AITask.created_at.asc(), AITask.id.asc()).with_for_update().first()


def _mark_task_failed(db: Session, task_id: int, task_type: str, error_message: str) -> None:
    task = db.query(AITask).filter(
        AITask.id == task_id,
        AITask.task_type == task_type,
    ).first()
    if not task:
        return

    task.status = "failed"
    task.completed_at = datetime.now()
    task.error_message = error_message
    db.commit()


def _recover_stale_processing_tasks(session: Session) -> None:
    deadline = datetime.now() - timedelta(seconds=PROCESSING_STALE_TIMEOUT_SECONDS)
    stale_tasks = session.query(AITask).filter(
        AITask.task_type.in_(tuple(PAPER_GENERATION_TASK_TYPES)),
        AITask.status == "processing",
        (
            (AITask.started_at.is_(None) & (AITask.created_at <= deadline))
            | (AITask.started_at <= deadline)
        ),
    ).all()
    if not stale_tasks:
        return

    recovered_ids = []
    for task in stale_tasks:
        task.status = "pending"
        task.started_at = None
        task.completed_at = None
        task.error_message = "任务处理超时，已自动恢复并重新入队"
        recovered_ids.append(task.id)
    session.commit()
    logger.warning("检测到 {} 个 AI 自动生成试卷类任务卡住，已自动恢复: {}", len(recovered_ids), recovered_ids)


def _acquire_dispatch_lock():
    try:
        redis_client = get_redis()
        lock = redis_client.lock(PAPER_GENERATION_DISPATCH_LOCK, timeout=30, blocking_timeout=5)
        if not lock.acquire(blocking=True):
            logger.warning("获取 AI 自动生成试卷类调度锁失败")
            return None
        return lock
    except Exception as exc:
        logger.warning("获取 AI 自动生成试卷类调度锁异常，改为无锁调度: {}", exc)
        return None
