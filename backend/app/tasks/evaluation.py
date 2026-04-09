"""
评价模块 Celery 任务
"""
from app.database import SessionLocal
from app.services.evaluation import EvaluationService
from celery_app import celery_app
from logger import logger


@celery_app.task(name="app.tasks.evaluation.trigger_training_evaluation")
def trigger_training_evaluation(training_id: int) -> None:
    """结班时自动创建评价任务并通知学员"""
    db = SessionLocal()
    try:
        task_id = EvaluationService(db).trigger_training_evaluation(training_id)
        if task_id:
            logger.info("自动评价任务已创建: training_id=%s, task_id=%s", training_id, task_id)
    except Exception as exc:
        logger.error("创建自动评价任务失败(training_id=%s): %s", training_id, exc)
    finally:
        db.close()
