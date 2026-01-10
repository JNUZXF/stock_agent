# app/agents/base_agent.py
# Agent基类 - 定义Agent的通用接口和行为

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from openai import OpenAI
import logging

from app.core.config import settings
from app.agents.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类
    
    定义Agent的通用接口,子类需要实现具体的工具和提示词
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """初始化Agent
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key or settings.DOUBAO_API_KEY
        self.base_url = base_url or settings.DOUBAO_BASE_URL
        self.model = model or settings.DOUBAO_MODEL
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        # 对话历史
        self.conversations: List[Dict[str, Any]] = []
        
        # 工具映射
        self.tools: Dict[str, BaseTool] = {}
        
        # 初始化
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """初始化Agent(子类实现)
        
        在此方法中:
        - 设置系统提示词
        - 注册工具
        - 初始化其他资源
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词(子类实现)
        
        Returns:
            系统提示词
        """
        pass
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册工具
        
        Args:
            tool: 工具实例
        """
        definition = tool.get_definition()
        tool_name = definition.get("name")
        
        if not tool_name:
            raise ValueError("工具定义必须包含name字段")
        
        self.tools[tool_name] = tool
        logger.info(f"注册工具: {tool_name}")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义
        
        Returns:
            工具定义列表
        """
        return [tool.get_definition() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 当工具不存在时
        """
        if tool_name not in self.tools:
            raise ValueError(f"未知的工具: {tool_name}")
        
        tool = self.tools[tool_name]
        return await tool(**kwargs)
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """添加消息到对话历史
        
        Args:
            role: 消息角色
            content: 消息内容
            **kwargs: 其他消息字段
        """
        message = {
            "role": role,
            "content": content,
            **kwargs
        }
        self.conversations.append(message)
    
    def clear_history(self) -> None:
        """清空对话历史(保留系统提示词)"""
        system_messages = [
            msg for msg in self.conversations
            if msg.get("role") == "system"
        ]
        self.conversations = system_messages
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Returns:
            对话历史列表
        """
        return self.conversations.copy()
    
    @abstractmethod
    async def chat(self, user_message: str) -> Generator[str, None, None]:
        """与Agent聊天(子类实现)
        
        Args:
            user_message: 用户消息
            
        Yields:
            流式响应内容
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息
        
        Returns:
            统计信息字典
        """
        tool_stats = {
            name: tool.get_stats()
            for name, tool in self.tools.items()
        }
        
        return {
            "model": self.model,
            "conversation_length": len(self.conversations),
            "tools": tool_stats
        }
