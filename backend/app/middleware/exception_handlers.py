from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas import StandardResponse
from logger import logger

# HTTPException处理器
async def http_exception_handler(request: Request, exc: HTTPException):
    """将HTTPException转换为标准响应格式"""
    if exc.status_code == 500:
        logger.exception(f"HTTP异常: {exc.status_code} - {exc.detail}")
    elif exc.status_code in (401, 403):
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    else:
        logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=200,
        content=StandardResponse(
            code=exc.status_code,
            message=exc.detail,
            data=None
        ).dict()
    )

# 请求验证错误处理器
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将请求验证错误转换为标准响应格式"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    logger.error(f"请求验证错误: {error_details}")
    return JSONResponse(
        status_code=200,
        content=StandardResponse(
            code=422,
            message="请求数据格式错误",
            data=None
        ).dict()
    )

# 通用异常处理器
async def general_exception_handler(request: Request, exc: Exception):
    """将通用异常转换为标准响应格式"""
    logger.exception(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=200,
        content=StandardResponse(
            code=500,
            message="服务器内部错误",
            data=None
        ).dict()
    )

def register_exception_handlers(app):
    """注册所有异常处理器到FastAPI应用"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 