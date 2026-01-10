# app/api/v1/routes/conversations.py
# 会话管理路由 - 处理会话相关的API请求

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.api.v1.schemas import (
    ConversationSummary,
    ConversationDetail,
    ConversationsResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
    MessageSchema
)
from app.api.deps import get_db_session
from app.services.conversation_service import ConversationService
from app.utils.validators import validate_pagination

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationsResponse)
async def get_conversations(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    keyword: str = Query(None, description="搜索关键词"),
    session: AsyncSession = Depends(get_db_session)
):
    """获取会话列表
    
    支持分页和搜索
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        keyword: 搜索关键词
        session: 数据库会话
        
    Returns:
        会话列表
    """
    try:
        # 验证分页参数
        skip, limit = validate_pagination(skip, limit)
        
        # 创建会话服务
        conv_service = ConversationService(session)
        
        # 根据是否有关键词选择查询方法
        if keyword:
            conversations = await conv_service.search_conversations(keyword, limit)
        else:
            conversations = await conv_service.get_recent_conversations(limit)
        
        # 转换为响应模型
        summaries = []
        for conv in conversations:
            # 获取消息数量
            messages = await conv_service.get_conversation_messages(conv.id)
            
            summary = ConversationSummary(
                id=conv.id,
                title=conv.title,
                summary=conv.summary,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(messages)
            )
            summaries.append(summary)
        
        return ConversationsResponse(
            conversations=summaries,
            total=len(summaries)
        )
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """获取会话详情
    
    包含会话信息和所有消息
    
    Args:
        conversation_id: 会话ID
        session: 数据库会话
        
    Returns:
        会话详情
    """
    try:
        conv_service = ConversationService(session)
        
        # 获取会话
        conversation = await conv_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"会话不存在: {conversation_id}"
            )
        
        # 获取消息
        messages = await conv_service.get_conversation_messages(conversation_id)
        
        # 转换消息模型
        message_schemas = [
            MessageSchema.model_validate(msg)
            for msg in messages
        ]
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_schemas
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取会话详情失败: {str(e)}"
        )


@router.post("", response_model=ConversationSummary, status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """创建新会话
    
    Args:
        request: 创建请求
        session: 数据库会话
        
    Returns:
        创建的会话
    """
    try:
        conv_service = ConversationService(session)
        
        conversation = await conv_service.create_conversation(
            title=request.title
        )
        
        await session.commit()
        
        return ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0
        )
        
    except Exception as e:
        await session.rollback()
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建会话失败: {str(e)}"
        )


@router.patch("/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """更新会话
    
    Args:
        conversation_id: 会话ID
        request: 更新请求
        session: 数据库会话
        
    Returns:
        更新后的会话
    """
    try:
        conv_service = ConversationService(session)
        
        # 检查会话是否存在
        conversation = await conv_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"会话不存在: {conversation_id}"
            )
        
        # 更新标题
        if request.title is not None:
            conversation = await conv_service.update_conversation_title(
                conversation_id,
                request.title
            )
        
        # 更新摘要
        if request.summary is not None:
            conversation = await conv_service.update_conversation_summary(
                conversation_id,
                request.summary
            )
        
        await session.commit()
        
        # 获取消息数量
        messages = await conv_service.get_conversation_messages(conversation_id)
        
        return ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"更新会话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"更新会话失败: {str(e)}"
        )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """删除会话
    
    Args:
        conversation_id: 会话ID
        session: 数据库会话
    """
    try:
        conv_service = ConversationService(session)
        
        success = await conv_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"会话不存在: {conversation_id}"
            )
        
        await session.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"删除会话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"删除会话失败: {str(e)}"
        )
