# app/api/v1/schemas/conversation.py
# 会话相关的Pydantic模型

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageSchema(BaseModel):
    """消息模型"""
    
    id: int = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色: user|assistant|system")
    content: Optional[str] = Field(None, description="消息内容")
    message_type: Optional[str] = Field(None, description="消息类型")
    created_at: datetime = Field(..., description="创建时间")
    
    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    """会话摘要模型"""
    
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    summary: Optional[str] = Field(None, description="会话摘要")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    message_count: int = Field(default=0, description="消息数量")
    
    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    """会话详情模型"""
    
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    summary: Optional[str] = Field(None, description="会话摘要")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: List[MessageSchema] = Field(default_factory=list, description="消息列表")
    
    model_config = {"from_attributes": True}


class ConversationsResponse(BaseModel):
    """会话列表响应模型"""
    
    conversations: List[ConversationSummary] = Field(
        default_factory=list,
        description="会话列表"
    )
    total: int = Field(..., description="总数")


class CreateConversationRequest(BaseModel):
    """创建会话请求模型"""
    
    title: str = Field(
        default="新会话",
        description="会话标题",
        max_length=200
    )


class UpdateConversationRequest(BaseModel):
    """更新会话请求模型"""
    
    title: Optional[str] = Field(
        None,
        description="会话标题",
        max_length=200
    )
    summary: Optional[str] = Field(
        None,
        description="会话摘要"
    )
