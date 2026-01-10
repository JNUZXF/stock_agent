# app/repositories/conversation_repo.py
# 会话Repository - 处理会话相关的数据访问

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """会话Repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)
    
    async def get_recent(self, limit: int = 20) -> List[Conversation]:
        """获取最近的会话列表
        
        Args:
            limit: 返回数量
            
        Returns:
            会话列表(按创建时间倒序)
        """
        stmt = (
            select(Conversation)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def search_by_title(self, keyword: str, limit: int = 20) -> List[Conversation]:
        """根据标题搜索会话
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
            
        Returns:
            匹配的会话列表
        """
        stmt = (
            select(Conversation)
            .where(Conversation.title.ilike(f"%{keyword}%"))
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        """更新会话标题
        
        Args:
            conversation_id: 会话ID
            title: 新标题
            
        Returns:
            更新后的会话或None
        """
        return await self.update(conversation_id, title=title)
    
    async def update_summary(self, conversation_id: str, summary: str) -> Optional[Conversation]:
        """更新会话摘要
        
        Args:
            conversation_id: 会话ID
            summary: 摘要内容
            
        Returns:
            更新后的会话或None
        """
        return await self.update(conversation_id, summary=summary)
