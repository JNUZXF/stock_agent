# app/services/conversation_service.py
# 会话服务 - 处理会话相关的业务逻辑

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.utils.id_generator import generate_conversation_id
from app.core.metrics import metrics_service

logger = logging.getLogger(__name__)


class ConversationService:
    """会话服务类
    
    处理会话的创建、查询、更新等业务逻辑
    """
    
    def __init__(self, session: AsyncSession):
        """初始化服务
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
    
    async def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        title: str = "新会话",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """创建新会话
        
        Args:
            conversation_id: 会话ID(可选,不提供则自动生成)
            title: 会话标题
            metadata: 元数据
            
        Returns:
            创建的会话对象
        """
        if not conversation_id:
            conversation_id = generate_conversation_id()
        
        conversation = await self.conversation_repo.create(
            id=conversation_id,
            title=title,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        # 记录指标
        metrics_service.record_conversation_created()
        
        logger.info(
            f"创建会话成功",
            extra={
                "conversation_id": conversation_id,
                "title": title
            }
        )
        
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取会话详情
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            会话对象或None
        """
        return await self.conversation_repo.get_by_id(conversation_id)
    
    async def get_recent_conversations(self, limit: int = 20) -> List[Conversation]:
        """获取最近的会话列表
        
        Args:
            limit: 返回数量
            
        Returns:
            会话列表
        """
        return await self.conversation_repo.get_recent(limit)
    
    async def search_conversations(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Conversation]:
        """搜索会话
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
            
        Returns:
            匹配的会话列表
        """
        return await self.conversation_repo.search_by_title(keyword, limit)
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str
    ) -> Optional[Conversation]:
        """更新会话标题
        
        Args:
            conversation_id: 会话ID
            title: 新标题
            
        Returns:
            更新后的会话或None
        """
        conversation = await self.conversation_repo.update_title(
            conversation_id,
            title
        )
        
        if conversation:
            logger.info(
                f"更新会话标题",
                extra={
                    "conversation_id": conversation_id,
                    "title": title
                }
            )
        
        return conversation
    
    async def update_conversation_summary(
        self,
        conversation_id: str,
        summary: str
    ) -> Optional[Conversation]:
        """更新会话摘要
        
        Args:
            conversation_id: 会话ID
            summary: 摘要内容
            
        Returns:
            更新后的会话或None
        """
        return await self.conversation_repo.update_summary(
            conversation_id,
            summary
        )
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            是否删除成功
        """
        success = await self.conversation_repo.delete(conversation_id)
        
        if success:
            metrics_service.record_conversation_closed()
            logger.info(
                f"删除会话",
                extra={"conversation_id": conversation_id}
            )
        
        return success
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: Optional[str] = None
    ) -> Message:
        """添加消息到会话
        
        Args:
            conversation_id: 会话ID
            role: 消息角色
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据
            
        Returns:
            创建的消息对象
        """
        message = await self.message_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        
        # 记录指标
        metrics_service.record_message(role)
        
        logger.debug(
            f"添加消息",
            extra={
                "conversation_id": conversation_id,
                "role": role,
                "content_length": len(content) if content else 0
            }
        )
        
        return message
    
    async def get_conversation_messages(
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
            消息列表
        """
        return await self.message_repo.get_by_conversation(
            conversation_id,
            skip,
            limit
        )
    
    async def get_conversation_with_messages(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取会话及其所有消息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            包含会话和消息的字典,或None
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        messages = await self.get_conversation_messages(conversation_id)
        
        return {
            "conversation": conversation,
            "messages": messages
        }
