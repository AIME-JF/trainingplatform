"""
请求日志中间件
记录每个HTTP请求的IP来源、端口和处理时间
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logger import logger


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    支持从反向代理头部获取
    """
    # 优先从 X-Forwarded-For 获取（多层代理场景）
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For 格式: client, proxy1, proxy2
        return x_forwarded_for.split(",")[0].strip()
    
    # 其次从 X-Real-IP 获取（Nginx 常用配置）
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    
    # 最后使用直连IP
    if request.client:
        return request.client.host
    
    return "unknown"


def get_client_port(request: Request) -> int | str:
    """获取客户端端口"""
    if request.client:
        return request.client.port
    return "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    # 慢请求阈值（毫秒）
    SLOW_REQUEST_THRESHOLD_MS = 1000
    
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = get_client_ip(request)
        client_port = get_client_port(request)
        method = request.method
        path = request.url.path
        
        # 记录请求开始
        start_time = time.time()
        logger.info(f"[{client_ip}:{client_port}] --> {method} {path}")
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = (time.time() - start_time) * 1000  # 毫秒
            
            # 记录请求结束
            logger.info(
                f"[{client_ip}:{client_port}] <-- {method} {path} "
                f"| {response.status_code} | {process_time:.2f}ms"
            )
            
            # 慢请求告警
            if process_time > self.SLOW_REQUEST_THRESHOLD_MS:
                logger.warning(
                    f"[SLOW REQUEST] [{client_ip}:{client_port}] {method} {path} "
                    f"| {response.status_code} | {process_time:.2f}ms"
                )
            
            return response
        except Exception as e:
            # 记录请求异常
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{client_ip}:{client_port}] <-- {method} {path} "
                f"| ERROR | {process_time:.2f}ms | {str(e)}"
            )
            raise
