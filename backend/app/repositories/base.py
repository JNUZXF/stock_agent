# app/repositories/base.py
# Repository基类 - 封装数据访问逻辑

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.base import BaseModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Repository基类
    
    提供通用的CRUD操作,子类可以添加特定的查询方法
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """初始化Repository
        
        Args:
            model: 数据模型类
            session: 数据库会话
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """创建记录
        
        Args:
            **kwargs: 模型字段
            
        Returns:
            创建的模型实例
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug(f"创建 {self.model.__name__}: {instance}")
        return instance
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """获取所有记录
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            order_by: 排序字段
            
        Returns:
            模型实例列表
        """
        stmt = select(self.model).offset(skip).limit(limit)
        
        if order_by:
            if order_by.startswith("-"):
                # 降序
                field = order_by[1:]
                stmt = stmt.order_by(getattr(self.model, field).desc())
            else:
                # 升序
                stmt = stmt.order_by(getattr(self.model, order_by))
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的模型实例或None
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance:
            await self.session.flush()
            await self.session.refresh(instance)
            logger.debug(f"更新 {self.model.__name__}: {instance}")
        
        return instance
    
    async def delete(self, id: Any) -> bool:
        """删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
        
        if success:
            logger.debug(f"删除 {self.model.__name__} id={id}")
        
        return success
    
    async def exists(self, id: Any) -> bool:
        """检查记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            是否存在
        """
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def count(self, **filters) -> int:
        """统计记录数
        
        Args:
            **filters: 过滤条件
            
        Returns:
            记录数
        """
        stmt = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def filter_by(self, **filters) -> List[ModelType]:
        """根据条件过滤
        
        Args:
            **filters: 过滤条件
            
        Returns:
            模型实例列表
        """
        stmt = select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
