# tests/unit/test_services/test_conversation_service.py
# 会话服务单元测试

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation_service import ConversationService


@pytest.mark.unit
class TestConversationService:
    """会话服务测试类"""
    
    async def test_create_conversation(self, test_session: AsyncSession):
        """测试创建会话"""
        service = ConversationService(test_session)
        
        conversation = await service.create_conversation(
            title="测试会话"
        )
        
        assert conversation is not None
        assert conversation.title == "测试会话"
        assert conversation.id is not None
    
    async def test_get_conversation(
        self,
        test_session: AsyncSession,
        sample_conversation_data
    ):
        """测试获取会话"""
        service = ConversationService(test_session)
        
        # 创建会话
        created = await service.create_conversation(
            conversation_id=sample_conversation_data["id"],
            title=sample_conversation_data["title"]
        )
        await test_session.commit()
        
        # 获取会话
        conversation = await service.get_conversation(created.id)
        
        assert conversation is not None
        assert conversation.id == sample_conversation_data["id"]
        assert conversation.title == sample_conversation_data["title"]
    
    async def test_add_message(
        self,
        test_session: AsyncSession,
        sample_conversation_data,
        sample_message_data
    ):
        """测试添加消息"""
        service = ConversationService(test_session)
        
        # 创建会话
        conversation = await service.create_conversation(
            conversation_id=sample_conversation_data["id"],
            title=sample_conversation_data["title"]
        )
        await test_session.commit()
        
        # 添加消息
        message = await service.add_message(
            conversation_id=conversation.id,
            role=sample_message_data["role"],
            content=sample_message_data["content"]
        )
        await test_session.commit()
        
        assert message is not None
        assert message.conversation_id == conversation.id
        assert message.role == sample_message_data["role"]
        assert message.content == sample_message_data["content"]
    
    async def test_get_conversation_messages(
        self,
        test_session: AsyncSession,
        sample_conversation_data,
        sample_message_data
    ):
        """测试获取会话消息"""
        service = ConversationService(test_session)
        
        # 创建会话
        conversation = await service.create_conversation(
            conversation_id=sample_conversation_data["id"],
            title=sample_conversation_data["title"]
        )
        
        # 添加多条消息
        await service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="消息1"
        )
        await service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="消息2"
        )
        await test_session.commit()
        
        # 获取消息
        messages = await service.get_conversation_messages(conversation.id)
        
        assert len(messages) == 2
        assert messages[0].content == "消息1"
        assert messages[1].content == "消息2"
    
    async def test_delete_conversation(
        self,
        test_session: AsyncSession,
        sample_conversation_data
    ):
        """测试删除会话"""
        service = ConversationService(test_session)
        
        # 创建会话
        conversation = await service.create_conversation(
            conversation_id=sample_conversation_data["id"],
            title=sample_conversation_data["title"]
        )
        await test_session.commit()
        
        # 删除会话
        success = await service.delete_conversation(conversation.id)
        await test_session.commit()
        
        assert success is True
        
        # 验证已删除
        deleted = await service.get_conversation(conversation.id)
        assert deleted is None
