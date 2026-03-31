"""
日志配置文件
"""
import sys
from pathlib import Path
from loguru import logger

from config import settings


# 移除默认的logger
logger.remove()

# 日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 控制台输出
logger.add(
    sys.stdout,
    format=log_format,
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
)

# 文件输出
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

# 错误日志 - 文件名包含日期，如 2025-12-24.error.log
logger.add(
    log_path / "{time:YYYY-MM-DD}.error.log",
    format=log_format,
    level="ERROR",
    rotation="00:00",  # 每日零点切换到新文件
    retention="30 days",
)

# 所有日志 - 文件名包含日期，如 2025-12-24.app.log
logger.add(
    log_path / "{time:YYYY-MM-DD}.app.log",
    format=log_format,
    level="DEBUG" if settings.DEBUG else "INFO",
    rotation="00:00",  # 每日零点切换到新文件
    retention="7 days",
)

# 导出logger实例
__all__ = ["logger"] 