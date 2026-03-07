"""
数据库初始化模块
"""
from typing import Generator, Optional
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from config import settings
from logger import logger

# 创建同步引擎（延迟连接，不立即测试）
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=20,  # 增加基础连接池大小
    max_overflow=50,  # 增加溢出连接数
    pool_timeout=30,  # 连接超时时间
    pool_recycle=3600,  # 连接回收时间（1小时）
)

# 创建同步会话工厂
SessionLocal = sessionmaker(
    engine,
    class_=Session,
    expire_on_commit=False,
)

# 创建Base类
Base = declarative_base()

# 数据库连接测试标志
_db_tested = False


def test_db_connection() -> bool:
    """测试数据库连接（懒加载方式调用）"""
    global _db_tested
    if _db_tested:
        return True
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.all()[0][0] == 1:
                logger.info("Database connected successfully")
                _db_tested = True
                return True
            else:
                logger.error("Database connection failed")
                return False
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# 创建Redis连接
def create_redis_client() -> redis.Redis:
    """创建Redis客户端"""
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 测试连接
        client.ping()
        logger.info("Redis connected successfully")
        return client
        
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


def get_redis_client_with_retry(max_retries: int = 3) -> redis.Redis:
    """获取Redis客户端，带重试机制"""
    import time
    
    for attempt in range(max_retries):
        try:
            client = create_redis_client()
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis连接失败，已重试 {max_retries} 次: {e}")
                raise
            else:
                logger.warning(f"Redis连接失败，正在重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # 指数退避


# 全局Redis客户端（懒加载）
class RedisClient:
    """懒加载Redis客户端包装器"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """懒加载获取Redis客户端"""
        if self._client is None:
            self._client = get_redis_client_with_retry()
        return self._client
    
    @client.setter
    def client(self, value: Optional[redis.Redis]):
        self._client = value
    
    def retry(self):
        """重新创建Redis连接"""
        self._client = get_redis_client_with_retry()


redis_client = RedisClient()

def init_db():
    """初始化数据库"""
    try:
        # 导入所有模型，确保它们被注册
        from app.models import (
            User, Role, Permission, user_roles, role_permissions,
            Config, ConfigGroup,
            Course, Chapter, CourseProgress,
            Training, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem,
            Question, Exam, ExamQuestion, ExamRecord,
            Certificate, InstructorProfile, MediaFile
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return redis_client.client


def test_redis_connection() -> bool:
    """测试Redis连接"""
    try:
        if redis_client.client is None:
            logger.error("Redis client is not initialized")
            return False
        redis_client.client.ping()
        logger.info("Redis connection test successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False


__all__ = ["Base", "engine", "get_db", "init_db", "redis_client", "get_redis", "create_redis_client", "get_redis_client_with_retry", "test_redis_connection"] 