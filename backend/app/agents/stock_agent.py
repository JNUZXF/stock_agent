# app/agents/stock_agent.py
# 股票分析Agent - 重构后的实现

from typing import Generator, Optional
import json
import logging
import openai

from app.agents.base_agent import BaseAgent
from app.agents.tools import StockAnalysisTool, ArxivPaperTool
from app.agents.prompts import get_stock_agent_system_prompt

logger = logging.getLogger(__name__)


class StockAnalysisAgent(BaseAgent):
    """股票分析Agent
    
    专门用于股票分析的智能代理,支持:
    - 股票信息查询
    - 财务数据分析
    - 学术论文搜索
    """
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """初始化股票分析Agent
        
        Args:
            conversation_id: 会话ID
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.conversation_id = conversation_id
        super().__init__(api_key, base_url, model)
    
    def _initialize(self) -> None:
        """初始化Agent"""
        # 设置系统提示词
        system_prompt = self.get_system_prompt()
        self.conversations.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 注册工具
        self.register_tool(StockAnalysisTool())
        self.register_tool(ArxivPaperTool())
        
        logger.info(
            f"股票分析Agent初始化完成",
            extra={
                "conversation_id": self.conversation_id,
                "model": self.model,
                "tools": list(self.tools.keys())
            }
        )
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return get_stock_agent_system_prompt()
    
    async def chat(self, user_message: str) -> Generator[str, None, None]:
        """与Agent聊天
        
        Args:
            user_message: 用户消息
            
        Yields:
            流式响应内容
        """
        # 添加用户消息
        self.conversations.append({
            "type": "message",
            "role": "user",
            "content": user_message,
        })
        
        logger.info(
            f"收到用户消息",
            extra={
                "conversation_id": self.conversation_id,
                "message_length": len(user_message)
            }
        )
        
        # 第一轮请求:触发工具调用(如果需要)
        response = self.client.responses.create(
            model=self.model,
            input=self.conversations,
            stream=True,
            tools=self.get_tool_definitions(),
            extra_body={"thinking": {"type": "disabled"}}
        )
        
        response_type = None
        tool_call = None
        assistant_response = ""
        
        # 处理响应流
        for i, event in enumerate(response):
            # 第3个事件通常包含响应类型信息
            if i == 2:
                if type(event) == openai.types.responses.response_output_item_added_event.ResponseOutputItemAddedEvent:
                    if event.item.type == "function_call":
                        response_type = "function_call"
                        tool_call = True
                    else:
                        response_type = "stream"
            
            # 如果是流式响应,直接输出
            if hasattr(event, "delta") and response_type == "stream":
                assistant_response += event.delta
                yield event.delta
        
        # 处理工具调用循环
        while tool_call:
            call_id = event.response.output[0].call_id
            tool_name = event.response.output[0].name
            arguments = event.response.output[0].arguments
            
            logger.info(
                f"调用工具: {tool_name}",
                extra={
                    "conversation_id": self.conversation_id,
                    "tool_name": tool_name,
                    "arguments": arguments
                }
            )
            
            # 解析参数并执行工具
            try:
                call_arguments = json.loads(arguments)
                tool_output = await self.execute_tool(tool_name, **call_arguments)
            except Exception as e:
                logger.error(
                    f"工具执行失败: {tool_name}",
                    exc_info=True,
                    extra={
                        "conversation_id": self.conversation_id,
                        "error": str(e)
                    }
                )
                tool_output = f"工具执行失败: {str(e)}"
            
            # 添加工具输出到对话历史
            self.conversations.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(tool_output, ensure_ascii=False),
            })
            
            # 继续对话
            response = self.client.responses.create(
                model=self.model,
                previous_response_id=event.response.id,
                input=self.conversations,
                stream=True,
                tools=self.get_tool_definitions(),
                extra_body={"thinking": {"type": "disabled"}},
            )
            
            assistant_response = ""
            
            # 处理新的响应流
            for i, event in enumerate(response):
                if i == 2:
                    if type(event) == openai.types.responses.response_output_item_added_event.ResponseOutputItemAddedEvent:
                        if event.item.type == "function_call":
                            response_type = "function_call"
                            tool_call = True
                        else:
                            response_type = "stream"
                            tool_call = False
                
                if hasattr(event, "delta") and response_type == "stream":
                    assistant_response += event.delta
                    yield event.delta
        
        # 添加助手回复到对话历史
        if assistant_response:
            self.conversations.append({
                "role": "assistant",
                "content": assistant_response,
            })
            
            logger.info(
                f"生成助手回复",
                extra={
                    "conversation_id": self.conversation_id,
                    "response_length": len(assistant_response)
                }
            )
