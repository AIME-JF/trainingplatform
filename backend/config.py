"""
配置文件
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
load_dotenv(".env.dev", override=True)

class Settings(BaseSettings):
    """项目配置"""

    # 基础配置
    PROJECT_NAME: str = "警务训练平台"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 权限配置
    FIXED_PERMISSIONS: list = [
        "GET_CURRENT_USER",
        "CHANGE_PASSWORD",
    ]

    # API配置
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/police_training"
    DATABASE_ECHO: bool = False

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # MinIO配置
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "police-training-files"

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["*"]

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-please-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30天

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # 数据库迁移配置
    AUTO_MIGRATE_ON_STARTUP: bool = True

    # AI 任务并发与超时
    AI_TASK_MAX_CONCURRENCY: int = 5
    AI_TASK_TIMEOUT_MINUTES: int = 15

    # 视频关键帧抽取
    KEYFRAME_TASK_TIMEOUT_MINUTES: int = 10
    KEYFRAME_BASE_INTERVAL_SECONDS: int = 15
    KEYFRAME_MAX_PER_MINUTE: int = 6
    KEYFRAME_THUMBNAIL_HEIGHT: int = 480
    KEYFRAME_THUMBNAIL_FPS: int = 5
    KEYFRAME_JPEG_QUALITY: int = 80

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "off", "no"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "on", "yes"}:
                return True
        return value


    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
