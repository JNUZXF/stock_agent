# app/api/v1/routes/health.py
# 健康检查路由

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
import logging

from app.core.database import check_db_health
from app.core.cache import check_redis_health
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
    environment: str
    dependencies: Dict[str, str]


@router.get("", response_model=HealthResponse)
async def health_check():
    """健康检查端点
    
    检查应用和依赖服务的健康状态
    
    Returns:
        健康状态信息
    """
    # 检查数据库
    db_healthy = await check_db_health()
    db_status = "healthy" if db_healthy else "unhealthy"
    
    # 检查Redis
    redis_healthy = await check_redis_health()
    redis_status = "healthy" if redis_healthy else "unhealthy"
    
    # 整体状态
    overall_status = "healthy" if (db_healthy and redis_healthy) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        dependencies={
            "database": db_status,
            "redis": redis_status
        }
    )


@router.get("/liveness")
async def liveness():
    """存活探针
    
    用于Kubernetes liveness probe
    
    Returns:
        简单的OK响应
    """
    return {"status": "ok"}


@router.get("/readiness")
async def readiness():
    """就绪探针
    
    用于Kubernetes readiness probe
    检查应用是否准备好接收流量
    
    Returns:
        就绪状态
    """
    # 检查关键依赖
    db_healthy = await check_db_health()
    
    if not db_healthy:
        return {"status": "not_ready", "reason": "database_unavailable"}
    
    return {"status": "ready"}
