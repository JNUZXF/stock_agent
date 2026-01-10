# app/api/middleware/error_handler.py
# 统一错误处理中间件

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.metrics import metrics_service

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器
    
    Args:
        request: HTTP请求
        exc: HTTP异常
        
    Returns:
        JSON响应
    """
    logger.warning(
        f"HTTP异常: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "url": str(request.url)
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception"
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器
    
    Args:
        request: HTTP请求
        exc: 验证异常
        
    Returns:
        JSON响应
    """
    errors = exc.errors()
    
    logger.warning(
        f"请求验证失败",
        extra={
            "url": str(request.url),
            "errors": errors
        }
    )
    
    # 格式化错误信息
    formatted_errors = []
    for error in errors:
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "请求参数验证失败",
                "type": "validation_error",
                "details": formatted_errors
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常
        
    Returns:
        JSON响应
    """
    logger.error(
        f"未处理的异常: {type(exc).__name__}",
        exc_info=True,
        extra={
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    # 记录异常指标
    metrics_service.record_exception(type(exc).__name__)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "服务器内部错误",
                "type": "internal_error"
            }
        }
    )
