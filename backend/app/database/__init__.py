"""
Database initialization helpers.
"""
from typing import Generator, Optional

import redis
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.schema import CreateColumn

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


SCHEMA_BOOTSTRAP_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "exams": (
        "scene",
        "participant_mode",
        "department_ids",
        "police_type_ids",
        "participant_summary",
        "legacy_admission_exam_id",
    ),
    "exam_participant_import_batches": (
        "id",
        "exam_id",
        "file_name",
        "status",
        "summary",
        "failure_rows",
        "created_by",
    ),
    "exam_participants": (
        "id",
        "exam_id",
        "user_id",
        "import_batch_id",
        "source_row_no",
        "source_snapshot",
        "match_status",
        "participation_status",
        "generated_password",
    ),
    "trainings": (
        "entry_exam_id",
    ),
    "library_items": (
        "plain_text_content",
    ),
    "knowledge_chat_sessions": (
        "knowledge_item_ids",
    ),
    "scenario_templates": (
        "knowledge_item_ids",
    ),
}


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


def _build_add_column_sql(table_name: str, column) -> str:
    """Build dialect-aware SQL for adding a missing column."""
    compiled_column = CreateColumn(column).compile(dialect=engine.dialect)
    quoted_table_name = engine.dialect.identifier_preparer.quote(table_name)
    return f"ALTER TABLE {quoted_table_name} ADD COLUMN {compiled_column}"


def bootstrap_declared_schema() -> None:
    """Backfill declared tables and critical columns outside the migration system."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        inspector = inspect(connection)

        for table_name in SCHEMA_BOOTSTRAP_REQUIREMENTS:
            metadata_table = Base.metadata.tables.get(table_name)
            if metadata_table is None:
                raise RuntimeError(f"模型中未声明表 `{table_name}`，无法完成启动补齐")

            if inspector.has_table(table_name):
                continue

            logger.warning(f"启动补齐：创建缺失表 `{table_name}`")
            metadata_table.create(bind=connection, checkfirst=True)

        inspector = inspect(connection)

        for table_name, required_columns in SCHEMA_BOOTSTRAP_REQUIREMENTS.items():
            metadata_table = Base.metadata.tables[table_name]
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }

            for column_name in required_columns:
                if column_name in existing_columns:
                    continue

                metadata_column = metadata_table.columns.get(column_name)
                if metadata_column is None:
                    raise RuntimeError(
                        f"模型中未声明字段 `{table_name}.{column_name}`，无法完成启动补齐"
                    )

                ddl = _build_add_column_sql(table_name, metadata_column)
                logger.warning(f"启动补齐：执行 {ddl}")
                connection.execute(text(ddl))

        inspector = inspect(connection)
        issues: list[str] = []
        for table_name, required_columns in SCHEMA_BOOTSTRAP_REQUIREMENTS.items():
            if not inspector.has_table(table_name):
                issues.append(f"缺少表 `{table_name}`")
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            missing_columns = [
                column_name
                for column_name in required_columns
                if column_name not in existing_columns
            ]
            if missing_columns:
                issues.append(
                    f"表 `{table_name}` 缺少字段: {', '.join(missing_columns)}"
                )

        if issues:
            detail_lines = "\n".join(f"- {issue}" for issue in issues)
            raise RuntimeError(f"统一考试启动补齐后仍有缺失结构。\n{detail_lines}")


def init_db():
    """Create declared tables and backfill critical bootstrap columns."""
    try:
        bootstrap_declared_schema()
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
