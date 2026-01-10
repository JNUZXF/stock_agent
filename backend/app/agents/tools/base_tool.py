# app/agents/tools/base_tool.py
# Agent工具基类 - 定义统一的工具接口

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基类
    
    所有Agent工具必须继承此类并实现execute方法
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.call_count = 0
        self.total_duration = 0.0
    
    @abstractmethod
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义(用于API调用)
        
        Returns:
            工具定义字典
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        pass
    
    async def __call__(self, **kwargs) -> Any:
        """调用工具(带性能统计)
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        start_time = time.time()
        self.call_count += 1
        
        try:
            logger.info(f"执行工具: {self.name}, 参数: {kwargs}")
            result = await self.execute(**kwargs)
            duration = time.time() - start_time
            self.total_duration += duration
            
            logger.info(
                f"工具执行成功: {self.name}",
                extra={
                    "tool_name": self.name,
                    "duration": duration,
                    "call_count": self.call_count
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"工具执行失败: {self.name}, 错误: {e}",
                exc_info=True,
                extra={
                    "tool_name": self.name,
                    "duration": duration,
                    "error": str(e)
                }
            )
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计信息
        
        Returns:
            统计信息字典
        """
        avg_duration = (
            self.total_duration / self.call_count
            if self.call_count > 0
            else 0.0
        )
        
        return {
            "name": self.name,
            "call_count": self.call_count,
            "total_duration": self.total_duration,
            "avg_duration": avg_duration
        }
