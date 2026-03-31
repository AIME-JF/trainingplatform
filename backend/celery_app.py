"""
Celery配置文件
"""
from celery import Celery
from config import settings

# 创建Celery实例
celery_app = Celery(
    "police_training",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_question",
        "app.tasks.ai_schedule",
        "app.tasks.ai_paper_assembly",
        "app.tasks.teaching_resource_generation",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化方式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果过期时间
    result_expires=3600,

    # 任务执行配置
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Redis Broker配置
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    broker_pool_limit=10,

    # 任务结果配置
    result_backend_transport_options={
        'retry_on_timeout': True,
        'socket_keepalive': True,
    },

    # Worker配置
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=50,
    worker_pool='gevent',
    worker_concurrency=100,
)
