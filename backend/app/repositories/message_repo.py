# app/repositories/message_repo.py
# 消息Repository - 处理消息相关的数据访问

from typing import List, Optional
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.message import Message
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class MessageRepository(BaseRepository[Message]):
    """消息Repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)
    
    async def get_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """获取会话的所有消息
        
        Args:
            conversation_id: 会话ID
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            消息列表(按创建时间升序)
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_by_conversation(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """获取会话的最新消息
        
        Args:
            conversation_id: 会话ID
            limit: 返回数量
            
        Returns:
            最新消息列表(按创建时间倒序)
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        # 反转顺序,使其按时间升序
        return list(reversed(messages))
    
    async def count_by_conversation(self, conversation_id: str) -> int:
        """统计会话的消息数
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            消息数量
        """
        return await self.count(conversation_id=conversation_id)
    
    async def get_by_role(
        self,
        conversation_id: str,
        role: str
    ) -> List[Message]:
        """获取会话中特定角色的消息
        
        Args:
            conversation_id: 会话ID
            role: 消息角色
            
        Returns:
            消息列表
        """
        stmt = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == role
                )
            )
            .order_by(Message.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_by_conversation(self, conversation_id: str) -> int:
        """删除会话的所有消息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            删除的消息数量
        """
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        count = 0
        for message in messages:
            await self.session.delete(message)
            count += 1
        
        logger.debug(f"删除会话 {conversation_id} 的 {count} 条消息")
        return count
