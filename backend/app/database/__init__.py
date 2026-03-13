"""
Database initialization helpers.
"""
from typing import Generator, Optional

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import settings
from logger import logger


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    engine,
    class_=Session,
    expire_on_commit=False,
)

Base = declarative_base()

_db_tested = False


def test_db_connection() -> bool:
    """Test the primary database connection lazily."""
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

            logger.error("Database connection failed")
            return False
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def create_redis_client() -> redis.Redis:
    """Create a Redis client and validate connectivity."""
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
            health_check_interval=30,
        )

        client.ping()
        logger.info("Redis connected successfully")
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


def get_redis_client_with_retry(max_retries: int = 3) -> redis.Redis:
    """Create a Redis client with exponential backoff retry."""
    import time

    for attempt in range(max_retries):
        try:
            return create_redis_client()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis connection failed after {max_retries} retries: {e}")
                raise

            logger.warning(
                f"Redis connection failed, retrying ({attempt + 1}/{max_retries}): {e}"
            )
            time.sleep(2 ** attempt)


class RedisClient:
    """Lazy Redis client wrapper."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = get_redis_client_with_retry()
        return self._client

    @client.setter
    def client(self, value: Optional[redis.Redis]):
        self._client = value

    def retry(self):
        self._client = get_redis_client_with_retry()


redis_client = RedisClient()


def init_db():
    """Create any declared tables that are still missing."""
    try:
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
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
    """Get the shared Redis client."""
    return redis_client.client


def test_redis_connection() -> bool:
    """Test Redis connectivity."""
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


__all__ = [
    "Base",
    "engine",
    "get_db",
    "init_db",
    "redis_client",
    "get_redis",
    "create_redis_client",
    "get_redis_client_with_retry",
    "test_redis_connection",
]
