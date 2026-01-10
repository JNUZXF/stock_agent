# app/services/agent_service.py
# Agent服务 - 管理Agent实例和对话处理

from typing import Dict, Optional, Generator
import logging

from app.agents.stock_agent import StockAnalysisAgent
from app.utils.id_generator import generate_conversation_id
from app.core.metrics import metrics_service

logger = logging.getLogger(__name__)


class AgentService:
    """Agent服务类
    
    管理Agent实例的生命周期和对话处理
    """
    
    def __init__(self):
        """初始化服务"""
        self.agents: Dict[str, StockAnalysisAgent] = {}
        self.max_agents = 1000  # 最大Agent实例数
    
    def get_or_create_agent(
        self,
        conversation_id: Optional[str] = None
    ) -> StockAnalysisAgent:
        """获取或创建Agent实例
        
        Args:
            conversation_id: 会话ID(可选)
            
        Returns:
            Agent实例
        """
        # 如果提供了conversation_id且已存在,直接返回
        if conversation_id and conversation_id in self.agents:
            logger.debug(f"复用Agent实例: {conversation_id}")
            return self.agents[conversation_id]
        
        # 生成新的conversation_id(如果未提供)
        if not conversation_id:
            conversation_id = generate_conversation_id()
        
        # 检查Agent数量限制
        if len(self.agents) >= self.max_agents:
            # 移除最旧的Agent(简单的LRU策略)
            oldest_id = next(iter(self.agents))
            self.remove_agent(oldest_id)
            logger.warning(
                f"Agent数量达到上限,移除最旧的Agent",
                extra={"removed_id": oldest_id}
            )
        
        # 创建新Agent
        agent = StockAnalysisAgent(conversation_id=conversation_id)
        self.agents[conversation_id] = agent
        
        # 记录指标
        metrics_service.record_agent_created()
        
        logger.info(
            f"创建Agent实例",
            extra={
                "conversation_id": conversation_id,
                "total_agents": len(self.agents)
            }
        )
        
        return agent
    
    def get_agent(self, conversation_id: str) -> Optional[StockAnalysisAgent]:
        """获取指定的Agent实例
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Agent实例或None
        """
        return self.agents.get(conversation_id)
    
    def remove_agent(self, conversation_id: str) -> bool:
        """移除Agent实例
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            是否成功移除
        """
        if conversation_id in self.agents:
            del self.agents[conversation_id]
            
            # 记录指标
            metrics_service.record_agent_destroyed()
            
            logger.info(
                f"移除Agent实例",
                extra={
                    "conversation_id": conversation_id,
                    "remaining_agents": len(self.agents)
                }
            )
            return True
        return False
    
    async def chat(
        self,
        conversation_id: Optional[str],
        message: str
    ) -> Generator[str, None, None]:
        """与Agent聊天
        
        Args:
            conversation_id: 会话ID
            message: 用户消息
            
        Yields:
            流式响应内容
        """
        # 获取或创建Agent
        agent = self.get_or_create_agent(conversation_id)
        
        # 调用Agent的chat方法
        async for chunk in agent.chat(message):
            yield chunk
    
    def get_agent_stats(self, conversation_id: str) -> Optional[Dict]:
        """获取Agent统计信息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            统计信息或None
        """
        agent = self.get_agent(conversation_id)
        if agent:
            return agent.get_stats()
        return None
    
    def get_service_stats(self) -> Dict:
        """获取服务统计信息
        
        Returns:
            服务统计信息
        """
        return {
            "total_agents": len(self.agents),
            "max_agents": self.max_agents,
            "agent_ids": list(self.agents.keys())
        }
    
    def clear_inactive_agents(self, max_age_seconds: int = 3600) -> int:
        """清理不活跃的Agent
        
        Args:
            max_age_seconds: 最大不活跃时间(秒)
            
        Returns:
            清理的Agent数量
        """
        # TODO: 实现基于时间的清理逻辑
        # 需要在Agent中记录最后活跃时间
        logger.info("清理不活跃Agent功能待实现")
        return 0


# 全局Agent服务实例
agent_service = AgentService()


def get_agent_service() -> AgentService:
    """获取Agent服务实例(用于依赖注入)
    
    Returns:
        Agent服务实例
    """
    return agent_service
