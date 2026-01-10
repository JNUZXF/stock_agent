# app/core/cache.py
# Redis缓存层 - 提供高性能数据缓存

from typing import Optional, Any
import json
import logging
from redis import asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局Redis客户端实例
_redis_client: Optional[Redis] = None
_connection_pool: Optional[ConnectionPool] = None


async def get_redis() -> Redis:
    """获取Redis客户端
    
    Returns:
        Redis异步客户端实例
    """
    global _redis_client, _connection_pool
    
    if _redis_client is None:
        try:
            # 创建连接池
            _connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=True,  # 自动解码为字符串
            )
            
            # 创建Redis客户端
            _redis_client = Redis(connection_pool=_connection_pool)
            
            # 测试连接
            await _redis_client.ping()
            
            logger.info(
                "Redis客户端已创建",
                extra={
                    "redis_url": settings.REDIS_URL.split("@")[-1],
                    "pool_size": settings.REDIS_POOL_SIZE
                }
            )
        except Exception as e:
            logger.error(f"Redis连接失败: {e}", exc_info=True)
            # 返回None,让调用者处理降级逻辑
            return None
    
    return _redis_client


async def close_redis() -> None:
    """关闭Redis连接"""
    global _redis_client, _connection_pool
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    
    if _connection_pool is not None:
        await _connection_pool.disconnect()
        _connection_pool = None
    
    logger.info("Redis连接已关闭")


async def check_redis_health() -> bool:
    """检查Redis健康状态
    
    Returns:
        Redis是否健康
    """
    try:
        redis = await get_redis()
        if redis is None:
            return False
        await redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
        return False


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def _get_redis(self) -> Optional[Redis]:
        """获取Redis客户端(内部方法)"""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值,不存在返回None
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return None
            
            value = await redis.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.warning(f"获取缓存失败 key={key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒),None表示使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            # 序列化值
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            
            # 使用默认TTL
            if ttl is None:
                ttl = settings.CACHE_TTL
            
            await redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"设置缓存失败 key={key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            await redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"删除缓存失败 key={key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            return await redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"检查缓存存在性失败 key={key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存
        
        Args:
            pattern: 键模式(支持通配符*)
            
        Returns:
            删除的键数量
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return 0
            
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"清除缓存模式失败 pattern={pattern}: {e}")
            return 0


# 全局缓存服务实例
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """获取缓存服务实例(用于依赖注入)"""
    return cache_service
