# app/main.py
# FastAPI应用主入口

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db, close_db
from app.core.cache import close_redis
from app.api.v1.routes import api_router
from app.api.middleware import (
    LoggingMiddleware,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# 设置日志系统
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    启动时初始化资源,关闭时清理资源
    """
    # 启动
    logger.info(
        f"应用启动",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    )
    
    # 初始化数据库(仅开发环境)
    if settings.is_development:
        try:
            await init_db()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.warning(f"数据库初始化失败(可能已存在): {e}")
    
    yield
    
    # 关闭
    logger.info("应用关闭中...")
    
    # 关闭数据库连接
    await close_db()
    
    # 关闭Redis连接
    await close_redis()
    
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="生产级股票分析智能体API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 注册异常处理器
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 向后兼容:保留原有API路径
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """根路径
    
    Returns:
        API信息
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else "disabled",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
