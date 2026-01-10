# app/api/v1/routes/chat.py
# 聊天路由 - 处理聊天相关的API请求

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Generator
import json
import logging

from app.api.v1.schemas import ChatRequest, ChatChunkResponse
from app.api.deps import get_agent_svc
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def format_sse_data(data: dict) -> bytes:
    """格式化SSE数据
    
    Args:
        data: 要发送的数据字典
        
    Returns:
        格式化的SSE字节串
    """
    json_str = json.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n".encode('utf-8')


@router.post("")
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_svc)
):
    """聊天接口
    
    支持流式输出,使用Server-Sent Events(SSE)
    
    Args:
        request: 聊天请求
        agent_service: Agent服务
        
    Returns:
        SSE流式响应
    """
    try:
        # 获取或创建Agent
        agent = agent_service.get_or_create_agent(request.conversation_id)
        conversation_id = agent.conversation_id
        
        async def generate_response() -> Generator[bytes, None, None]:
            """生成SSE流式响应"""
            try:
                # 流式调用Agent的chat方法
                async for chunk in agent.chat(request.message):
                    # 发送数据块
                    response_data = ChatChunkResponse(
                        type="chunk",
                        content=chunk,
                        conversation_id=conversation_id
                    )
                    yield format_sse_data(response_data.model_dump())
                
                # 发送完成信号
                done_data = ChatChunkResponse(
                    type="done",
                    conversation_id=conversation_id
                )
                yield format_sse_data(done_data.model_dump())
                
                logger.info(
                    f"聊天请求完成",
                    extra={
                        "conversation_id": conversation_id,
                        "message_length": len(request.message)
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"聊天处理错误",
                    exc_info=True,
                    extra={
                        "conversation_id": conversation_id,
                        "error": str(e)
                    }
                )
                # 发送错误信息
                error_data = ChatChunkResponse(
                    type="error",
                    error=str(e),
                    conversation_id=conversation_id
                )
                yield format_sse_data(error_data.model_dump())
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"聊天接口错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )
