# tests/e2e/test_chat_flow.py
# 端到端聊天流程测试

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.slow
class TestChatFlow:
    """聊天流程端到端测试"""
    
    async def test_complete_chat_flow(self, test_client: AsyncClient):
        """测试完整的聊天流程
        
        1. 发送聊天请求
        2. 接收流式响应
        3. 获取会话历史
        """
        # 1. 发送聊天请求
        chat_request = {
            "message": "你好,请介绍一下自己"
        }
        
        response = await test_client.post(
            "/api/v1/chat",
            json=chat_request
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # 2. 解析SSE响应
        conversation_id = None
        chunks = []
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                data = json.loads(line[6:])
                
                if data["type"] == "chunk":
                    chunks.append(data["content"])
                    if not conversation_id:
                        conversation_id = data.get("conversation_id")
                elif data["type"] == "done":
                    break
        
        assert conversation_id is not None
        assert len(chunks) > 0
        
        # 3. 获取会话历史
        history_response = await test_client.get(
            f"/api/v1/conversations/{conversation_id}"
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert history_data["id"] == conversation_id
        assert len(history_data["messages"]) >= 1
    
    async def test_multi_turn_conversation(self, test_client: AsyncClient):
        """测试多轮对话"""
        conversation_id = None
        
        # 第一轮对话
        response1 = await test_client.post(
            "/api/v1/chat",
            json={"message": "你好"}
        )
        
        assert response1.status_code == 200
        
        # 获取conversation_id
        async for line in response1.aiter_lines():
            if line.startswith("data: "):
                import json
                data = json.loads(line[6:])
                if data.get("conversation_id"):
                    conversation_id = data["conversation_id"]
                    break
        
        assert conversation_id is not None
        
        # 第二轮对话(使用相同的conversation_id)
        response2 = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "请继续",
                "conversation_id": conversation_id
            }
        )
        
        assert response2.status_code == 200
        
        # 验证会话历史包含两轮对话
        history_response = await test_client.get(
            f"/api/v1/conversations/{conversation_id}"
        )
        
        history_data = history_response.json()
        # 应该至少有2条用户消息
        user_messages = [
            msg for msg in history_data["messages"]
            if msg["role"] == "user"
        ]
        assert len(user_messages) >= 2
