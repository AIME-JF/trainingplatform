"""
视频关键帧抽取 Celery 任务。
串行执行，每次只处理一个任务。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal, get_redis
from app.models import VideoKeyframeTask
from app.services.video_keyframe import VideoKeyframeExtractor
from celery_app import celery_app
from logger import logger


KEYFRAME_DISPATCH_LOCK = "video:keyframe:dispatch-lock"
KEYFRAME_TASK_NAME = "app.tasks.video_keyframe.run_keyframe_extraction"


@celery_app.task(bind=True, name=KEYFRAME_TASK_NAME, max_retries=2)
def run_keyframe_extraction(self, task_id: int) -> None:
    """执行视频关键帧抽取任务"""
    db = SessionLocal()
    should_schedule_next = False

    try:
        task = db.query(VideoKeyframeTask).filter(VideoKeyframeTask.id == task_id).first()
        if not task:
            logger.warning("关键帧任务不存在: %s", task_id)
            return

        if task.status in {"success", "partial_success", "failed"}:
            logger.info("关键帧任务已结束，跳过: %s", task_id)
            return

        VideoKeyframeExtractor(db).execute(task_id)
        should_schedule_next = True
    except Exception as exc:
        db.rollback()
        logger.error("关键帧任务执行失败(task_id=%s, retry=%s): %s", task_id, self.request.retries, exc)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))

        _mark_task_failed(db, task_id, str(exc))
        should_schedule_next = True
    finally:
        db.close()

    if should_schedule_next:
        try:
            schedule_keyframe_task()
        except Exception as exc:
            logger.error("关键帧任务后续调度失败: %s", exc)


def schedule_keyframe_task(preferred_task_id: Optional[int] = None, db: Optional[Session] = None) -> Optional[int]:
    """调度下一个关键帧抽取任务（串行，同时只允许一个 running）"""
    lock = None
    own_session = db is None
    session = db or SessionLocal()

    try:
        lock = _acquire_dispatch_lock()

        # 串行：已有 running 任务则不调度
        if session.query(VideoKeyframeTask.id).filter(
            VideoKeyframeTask.status == "running",
        ).first():
            return None

        next_task = _pick_next_pending_task(session, preferred_task_id)
        if not next_task:
            return None

        next_task.status = "running"
        next_task.started_at = next_task.started_at or datetime.now()
        session.commit()

        try:
            run_keyframe_extraction.apply_async(
                args=[next_task.id],
                task_id=f"video-keyframe-task-{next_task.id}",
            )
        except Exception as exc:
            session.rollback()
            revert = session.query(VideoKeyframeTask).filter(VideoKeyframeTask.id == next_task.id).first()
            if revert:
                revert.status = "pending"
                revert.started_at = None
                revert.error_message = f"调度失败: {exc}"
                session.commit()
            logger.error("调度关键帧任务失败: %s", exc)
            return None

        logger.info("关键帧任务已加入 Celery: %s", next_task.id)
        return next_task.id
    finally:
        if lock is not None:
            try:
                lock.release()
            except Exception:
                pass
        if own_session:
            session.close()


def _pick_next_pending_task(session: Session, preferred_task_id: Optional[int]) -> Optional[VideoKeyframeTask]:
    if preferred_task_id:
        task = session.query(VideoKeyframeTask).filter(
            VideoKeyframeTask.id == preferred_task_id,
            VideoKeyframeTask.status == "pending",
        ).with_for_update().first()
        if task:
            return task

    return session.query(VideoKeyframeTask).filter(
        VideoKeyframeTask.status == "pending",
    ).order_by(VideoKeyframeTask.created_at.asc(), VideoKeyframeTask.id.asc()).with_for_update().first()


def _mark_task_failed(db: Session, task_id: int, error_message: str) -> None:
    task = db.query(VideoKeyframeTask).filter(VideoKeyframeTask.id == task_id).first()
    if not task:
        return
    task.status = "failed"
    task.completed_at = datetime.now()
    task.error_message = error_message[:2000]
    db.commit()


def _acquire_dispatch_lock():
    try:
        redis_client = get_redis()
        lock = redis_client.lock(KEYFRAME_DISPATCH_LOCK, timeout=30, blocking_timeout=5)
        if not lock.acquire(blocking=True):
            logger.warning("获取关键帧调度锁失败")
            return None
        return lock
    except Exception as exc:
        logger.warning("获取关键帧调度锁异常: %s", exc)
        return None
