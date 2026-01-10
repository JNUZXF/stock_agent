# app/core/database.py
# 数据库连接管理 - 使用SQLAlchemy 2.0异步引擎

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建声明式基类
Base = declarative_base()

# 全局引擎实例
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """获取数据库引擎
    
    Returns:
        SQLAlchemy异步引擎实例
    """
    global _engine
    
    if _engine is None:
        # 根据环境选择连接池策略
        if settings.is_development:
            poolclass = NullPool  # 开发环境使用NullPool,避免连接占用
        else:
            poolclass = QueuePool  # 生产环境使用连接池
        
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG and settings.is_development,  # 开发环境打印SQL
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,  # 连接前检查有效性
            poolclass=poolclass,
        )
        
        logger.info(
            "数据库引擎已创建",
            extra={
                "database_url": settings.DATABASE_URL.split("@")[-1],  # 隐藏密码
                "pool_size": settings.DATABASE_POOL_SIZE,
                "environment": settings.ENVIRONMENT
            }
        )
    
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """获取会话工厂
    
    Returns:
        异步会话工厂
    """
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后对象不过期
            autocommit=False,
            autoflush=False,
        )
        
        logger.info("数据库会话工厂已创建")
    
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话(用于依赖注入)
    
    Yields:
        数据库会话
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库(创建所有表)
    
    注意: 生产环境应使用Alembic进行数据库迁移
    """
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from app.models import conversation, message  # noqa
            
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """关闭数据库连接"""
    global _engine, _async_session_maker
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("数据库连接已关闭")


async def check_db_health() -> bool:
    """检查数据库健康状态
    
    Returns:
        数据库是否健康
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False
