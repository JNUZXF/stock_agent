# app/api/v1/schemas/chat.py
# 聊天相关的Pydantic模型

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求模型"""
    
    message: str = Field(
        ...,
        description="用户消息内容",
        min_length=1,
        max_length=10000
    )
    conversation_id: Optional[str] = Field(
        None,
        description="会话ID,不提供则创建新会话"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "分析一下SH600519这只股票",
                    "conversation_id": "20240115-143052123 45"
                }
            ]
        }
    }


class ChatChunkResponse(BaseModel):
    """流式响应数据块模型"""
    
    type: str = Field(
        ...,
        description="响应类型: chunk|done|error"
    )
    content: Optional[str] = Field(
        None,
        description="内容片段"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="会话ID"
    )
    error: Optional[str] = Field(
        None,
        description="错误信息"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "chunk",
                    "content": "贵州茅台是一家...",
                    "conversation_id": "20240115-143052123 45"
                }
            ]
        }
    }
