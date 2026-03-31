"""
Police training platform backend.
"""
__version__ = "1.0.0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.middleware import RequestLoggingMiddleware, register_exception_handlers
from app.schemas import StandardResponse
from app.views import all_routers
from config import settings
from logger import logger


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)


@app.get("/", response_model=StandardResponse)
def root():
    return StandardResponse(
        message="欢迎使用",
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
        },
    )


@app.get("/health", response_model=StandardResponse)
def health_check():
    return StandardResponse(
        message="系统运行正常",
        data={"status": "healthy"},
    )


for router in all_routers:
    app.include_router(router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def startup_event():
    logger.info("Starting up...")

    if settings.AUTO_MIGRATE_ON_STARTUP:
        try:
            from app.database.auto_migrate import run_auto_migration

            logger.info("Running automatic database migration...")
            migration_success = run_auto_migration()
            if migration_success:
                logger.info("Automatic database migration finished")
            else:
                logger.warning("Automatic database migration failed; schema compatibility will be validated before serving requests")
        except Exception as e:
            logger.error(f"Automatic database migration error: {e}")
            logger.warning("Schema compatibility will be validated before serving requests")
    else:
        logger.info("Automatic database migration is disabled")

    if settings.AUTO_MIGRATE_ON_STARTUP:
        try:
            from app.database.auto_migrate import (
                ensure_schema_compatibility,
                is_database_empty,
            )

            if is_database_empty():
                logger.info("Database is empty; skipping pre-init schema compatibility check and allowing bootstrap")
            else:
                logger.info("Validating critical database schema compatibility before table initialization...")
                ensure_schema_compatibility()
        except Exception as e:
            logger.error(f"Database schema compatibility check failed before table initialization: {e}")
            raise

    try:
        logger.info("Ensuring declared tables exist...")
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed during startup: {e}")
        raise

    if not settings.AUTO_MIGRATE_ON_STARTUP:
        try:
            from app.database.auto_migrate import ensure_schema_compatibility

            logger.info("Validating critical database schema compatibility after table initialization...")
            ensure_schema_compatibility()
        except Exception as e:
            logger.error(f"Database schema compatibility check failed after table initialization: {e}")
            raise

    try:
        from app.database import test_redis_connection

        if test_redis_connection():
            logger.info("Redis connected successfully")
        else:
            logger.warning("Redis connection check failed")
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down...")
