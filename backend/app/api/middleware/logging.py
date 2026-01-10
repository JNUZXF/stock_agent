# app/api/middleware/logging.py
# 请求日志中间件 - 记录所有HTTP请求

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

from app.utils.id_generator import generate_request_id
from app.core.logging import set_request_context, clear_request_context
from app.core.metrics import metrics_service

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件
    
    记录每个HTTP请求的详细信息
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            HTTP响应
        """
        # 生成请求ID
        request_id = generate_request_id()
        
        # 设置请求上下文
        set_request_context(request_id)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求开始
        logger.info(
            f"请求开始: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client_host": client_host,
                "user_agent": user_agent
            }
        )
        
        # 处理请求
        try:
            response: Response = await call_next(request)
            
            # 计算处理时间
            duration = time.time() - start_time
            
            # 提取响应信息
            status_code = response.status_code
            
            # 记录访问日志
            access_logger.info(
                f"{method} {url} {status_code} {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "duration": duration,
                    "client_host": client_host
                }
            )
            
            # 记录指标
            endpoint = request.url.path
            metrics_service.record_request(
                method=method,
                endpoint=endpoint,
                status=status_code,
                duration=duration
            )
            
            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # 计算处理时间
            duration = time.time() - start_time
            
            # 记录错误
            logger.error(
                f"请求处理失败: {method} {url}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "error": str(e)
                }
            )
            
            # 记录错误指标
            endpoint = request.url.path
            metrics_service.record_error(
                error_type=type(e).__name__,
                endpoint=endpoint
            )
            
            raise
            
        finally:
            # 清除请求上下文
            clear_request_context()
