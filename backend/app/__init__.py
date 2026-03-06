"""
警务训练平台后端
"""
__version__ = "1.0.0"

"""
FastAPI主应用文件
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager

from config import settings
from logger import logger
from app.database import init_db
from app.middleware import register_exception_handlers, RequestLoggingMiddleware
from app.middleware.auth import get_current_user, require_permission
from app.schemas import StandardResponse, TokenData
from app.views import all_routers


@contextmanager
def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting up...")
    init_db()
    yield
    # 关闭时
    logger.info("Shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 注册异常处理器
register_exception_handlers(app)


@app.get("/", response_model=StandardResponse)
def root():
    """根路径"""
    return StandardResponse(
        message="欢迎使用",
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs"
        }
    )


@app.get("/health", response_model=StandardResponse)
def health_check():
    """健康检查"""
    return StandardResponse(
        message="系统运行正常",
        data={"status": "healthy"}
    )


# 注册所有业务路由
for router in all_routers:
    app.include_router(router, prefix=settings.API_V1_STR)


# 应用启动时初始化数据库
@app.on_event("startup")
def startup_event():
    """启动事件"""
    logger.info("Starting up...")

    # 自动数据库迁移
    if settings.AUTO_MIGRATE_ON_STARTUP:
        try:
            from app.database.auto_migrate import run_auto_migration
            logger.info("启用自动数据库迁移...")

            migration_success = run_auto_migration()
            if migration_success:
                logger.info("自动数据库迁移完成")
            else:
                logger.warning("自动数据库迁移失败，继续启动应用")
        except Exception as e:
            logger.error(f"自动数据库迁移异常: {e}")
            logger.warning("迁移失败，尝试使用传统初始化方式...")
            init_db()
    else:
        logger.info("自动数据库迁移已禁用，使用传统初始化方式")
        init_db()

    # 测试Redis连接
    try:
        from app.database import test_redis_connection
        if test_redis_connection():
            logger.info("Redis连接成功")
        else:
            logger.warning("Redis连接失败")
    except Exception as e:
        logger.error(f"Redis连接测试失败: {str(e)}")


@app.on_event("shutdown")
def shutdown_event():
    """关闭事件"""
    logger.info("Shutting down...")
