"""
智能解析课表文件 - Celery 异步任务
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AITask
from celery_app import celery_app
from logger import logger

TASK_TYPE = "schedule_file_parse"
TASK_NAME = "app.tasks.schedule_file_parse.generate_schedule_file_parse_task"
LOCK_KEY = "schedule-file-parse:dispatch-lock"


def _pick_next_pending_task(session: Session, preferred_task_id: int | None = None) -> AITask | None:
    if preferred_task_id:
        task = session.query(AITask).filter(
            AITask.id == preferred_task_id,
            AITask.task_type == TASK_TYPE,
            AITask.status == "pending",
        ).first()
        if task:
            return task
    return session.query(AITask).filter(
        AITask.task_type == TASK_TYPE,
        AITask.status == "pending",
    ).order_by(asc(AITask.created_at), asc(AITask.id)).first()


def _mark_task_failed(session: Session, task_id: int, error_message: str) -> None:
    from app.services.schedule_file_parse import ScheduleFileParseService
    ScheduleFileParseService(session).mark_task_failed(task_id, error_message)


def _acquire_dispatch_lock() -> bool:
    try:
        from app.database import redis_client
        if redis_client is None:
            return True
        return bool(redis_client.set(LOCK_KEY, "1", nx=True, ex=120))
    except Exception:
        return True


def schedule_schedule_file_parse_task(
    preferred_task_id: int | None = None,
    db: Session | None = None,
) -> int | None:
    if not _acquire_dispatch_lock():
        return None

    session = db or SessionLocal()
    try:
        processing = session.query(AITask.id).filter(
            AITask.task_type == TASK_TYPE,
            AITask.status == "processing",
        ).first()
        if processing:
            return None

        task = _pick_next_pending_task(session, preferred_task_id)
        if not task:
            return None

        from datetime import datetime, timezone
        task.status = "processing"
        task.started_at = datetime.now(timezone.utc)
        session.commit()

        generate_schedule_file_parse_task.apply_async(
            args=[task.id],
            task_id=f"schedule-file-parse-task-{task.id}",
        )
        return task.id
    except Exception as exc:
        logger.opt(exception=True).error("调度智能解析课表任务异常: {}", exc)
        session.rollback()
        return None
    finally:
        if db is None:
            session.close()
        try:
            from app.database import redis_client
            if redis_client:
                redis_client.delete(LOCK_KEY)
        except Exception:
            pass


@celery_app.task(bind=True, name=TASK_NAME, max_retries=3)
def generate_schedule_file_parse_task(self, task_id: int) -> None:
    session = SessionLocal()
    try:
        from app.services.schedule_file_parse import ScheduleFileParseService
        ScheduleFileParseService(session).execute_task(task_id)
    except Exception as exc:
        logger.opt(exception=True).error("智能解析课表任务 {} 异常: {}", task_id, exc)
        if self.request.retries < self.max_retries:
            session.rollback()
            raise self.retry(exc=exc, countdown=3 * (self.request.retries + 1))
        _mark_task_failed(session, task_id, str(exc)[:2000])
    finally:
        # 调度下一个排队任务
        try:
            schedule_schedule_file_parse_task(db=session)
        except Exception:
            pass
        session.close()
