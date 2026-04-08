"""
AI 任务超时检查定时任务。

每分钟扫描所有 processing 状态且 started_at 超过配置超时时间的 AI 任务，
标记为 failed 并 revoke 对应的 Celery 任务，然后触发后续调度。
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import AITask
from celery_app import celery_app
from config import settings
from logger import logger


TASK_ID_PATTERNS = {
    "question_generation": "ai-question-task-{}",
    "paper_assembly": "ai-paper-assembly-task-{}",
    "schedule_generation": "ai-schedule-task-{}",
    "resource_generation": "teaching-resource-generation-task-{}",
}


@celery_app.task(name="app.tasks.ai_task_timeout.check_ai_task_timeout")
def check_ai_task_timeout() -> None:
    """扫描并处理超时的 AI 任务"""
    timeout_minutes = settings.AI_TASK_TIMEOUT_MINUTES
    if timeout_minutes <= 0:
        return

    cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
    db = SessionLocal()
    timed_out_types: set[str] = set()

    try:
        timed_out_tasks = db.query(AITask).filter(
            AITask.status == "processing",
            AITask.started_at < cutoff,
        ).all()

        if not timed_out_tasks:
            return

        for task in timed_out_tasks:
            logger.warning(
                "AI 任务超时(task_id=%s, type=%s, started_at=%s)，标记为失败",
                task.id, task.task_type, task.started_at,
            )

            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = f"任务超时（超过 {timeout_minutes} 分钟未完成）"
            timed_out_types.add(task.task_type)

            celery_task_id_pattern = TASK_ID_PATTERNS.get(task.task_type)
            if celery_task_id_pattern:
                celery_task_id = celery_task_id_pattern.format(task.id)
                try:
                    celery_app.control.revoke(celery_task_id, terminate=True)
                    logger.info("已 revoke Celery 任务: %s", celery_task_id)
                except Exception as exc:
                    logger.warning("revoke Celery 任务失败(id=%s): %s", celery_task_id, exc)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("AI 任务超时检查失败: %s", exc)
        return
    finally:
        db.close()

    _schedule_next_for_types(timed_out_types)


def _schedule_next_for_types(task_types: set[str]) -> None:
    """对超时清理涉及的任务类型触发后续调度"""
    schedulers = {
        "question_generation": "app.tasks.ai_question.schedule_question_task",
        "paper_assembly": "app.tasks.ai_paper_assembly.schedule_paper_assembly_task",
        "schedule_generation": "app.tasks.ai_schedule.schedule_ai_schedule_task",
        "resource_generation": "app.tasks.teaching_resource_generation.schedule_teaching_resource_generation_task",
    }

    for task_type in task_types:
        module_path = schedulers.get(task_type)
        if not module_path:
            continue
        try:
            module_name, func_name = module_path.rsplit(".", 1)
            import importlib
            mod = importlib.import_module(module_name)
            schedule_func = getattr(mod, func_name)
            for _ in range(settings.AI_TASK_MAX_CONCURRENCY):
                if not schedule_func():
                    break
            logger.info("超时清理后已触发 %s 后续调度", task_type)
        except Exception as exc:
            logger.error("超时清理后触发 %s 后续调度失败: %s", task_type, exc)
