# app/api/deps.py
# API依赖注入 - 提供通用的依赖项

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings, Settings
from app.core.cache import get_cache_service, CacheService
from app.core.metrics import get_metrics_service, MetricsService
from app.services.agent_service import get_agent_service, AgentService
from app.services.conversation_service import ConversationService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话
    
    Yields:
        数据库会话
    """
    async for session in get_db():
        yield session


def get_config() -> Settings:
    """获取配置
    
    Returns:
        配置实例
    """
    return get_settings()


def get_cache() -> CacheService:
    """获取缓存服务
    
    Returns:
        缓存服务实例
    """
    return get_cache_service()


def get_metrics() -> MetricsService:
    """获取指标服务
    
    Returns:
        指标服务实例
    """
    return get_metrics_service()


def get_agent_svc() -> AgentService:
    """获取Agent服务
    
    Returns:
        Agent服务实例
    """
    return get_agent_service()


async def get_conversation_service(
    session: AsyncSession = None
) -> ConversationService:
    """获取会话服务
    
    Args:
        session: 数据库会话
        
    Returns:
        会话服务实例
    """
    if session is None:
        async for session in get_db():
            return ConversationService(session)
    return ConversationService(session)
