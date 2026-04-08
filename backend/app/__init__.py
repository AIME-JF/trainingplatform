"""
Police training platform backend.
"""
__version__ = "1.0.0"

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query as WSQuery
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database import init_db
from app.middleware import RequestLoggingMiddleware, register_exception_handlers
from app.schemas import StandardResponse
from app.views import all_routers
from app.websocket import connect, disconnect
from app.services.auth import auth_service
from config import settings
from logger import logger


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Mount docs folder for template downloads
docs_path = Path(__file__).parent.parent.parent / "docs"
if docs_path.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_path)), name="docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)


@app.get("/", response_model=StandardResponse, tags=["system_public"])
def root():
    return StandardResponse(
        message="欢迎使用",
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
        },
    )


@app.get("/health", response_model=StandardResponse, tags=["system_public"])
def health_check():
    return StandardResponse(
        message="系统运行正常",
        data={"status": "healthy"},
    )


for router in all_routers:
    app.include_router(router, prefix=settings.API_V1_STR)


@app.websocket("/ws/trainings/{training_id}/activities")
async def ws_training_activities(
    websocket: WebSocket,
    training_id: int,
    token: str = WSQuery(default=""),
):
    if not token:
        await websocket.close(code=4001)
        return
    try:
        payload = auth_service.verify_token(token)
        if payload is None:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await connect(training_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(training_id, websocket)


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

    try:
        logger.info("Ensuring declared tables and bootstrap columns exist...")
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed during startup: {e}")
        raise

    try:
        from app.database.auto_migrate import ensure_schema_compatibility

        logger.info("Validating migration-tracked schema compatibility after bootstrap...")
        ensure_schema_compatibility()
    except Exception as e:
        logger.error(f"Database schema compatibility check failed after bootstrap: {e}")
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
