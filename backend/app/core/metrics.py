# app/core/metrics.py
# Prometheus监控指标 - 收集应用性能和业务指标

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建指标注册表
registry = CollectorRegistry()

# ==================== 请求指标 ====================

# HTTP请求总数
http_requests_total = Counter(
    name="http_requests_total",
    documentation="HTTP请求总数",
    labelnames=["method", "endpoint", "status"],
    registry=registry
)

# HTTP请求延迟
http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP请求延迟(秒)",
    labelnames=["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

# HTTP请求大小
http_request_size_bytes = Histogram(
    name="http_request_size_bytes",
    documentation="HTTP请求大小(字节)",
    labelnames=["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=registry
)

# HTTP响应大小
http_response_size_bytes = Histogram(
    name="http_response_size_bytes",
    documentation="HTTP响应大小(字节)",
    labelnames=["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=registry
)

# ==================== 业务指标 ====================

# 会话总数
conversations_total = Counter(
    name="conversations_total",
    documentation="创建的会话总数",
    registry=registry
)

# 消息总数
messages_total = Counter(
    name="messages_total",
    documentation="发送的消息总数",
    labelnames=["role"],  # user/assistant
    registry=registry
)

# 工具调用总数
tool_calls_total = Counter(
    name="tool_calls_total",
    documentation="工具调用总数",
    labelnames=["tool_name", "status"],  # status: success/error
    registry=registry
)

# 工具调用延迟
tool_call_duration_seconds = Histogram(
    name="tool_call_duration_seconds",
    documentation="工具调用延迟(秒)",
    labelnames=["tool_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry
)

# 活跃会话数
active_conversations = Gauge(
    name="active_conversations",
    documentation="当前活跃的会话数",
    registry=registry
)

# Agent实例数
active_agents = Gauge(
    name="active_agents",
    documentation="当前活跃的Agent实例数",
    registry=registry
)

# ==================== 系统指标 ====================

# 数据库连接池状态
db_pool_size = Gauge(
    name="db_pool_size",
    documentation="数据库连接池大小",
    registry=registry
)

db_pool_checked_out = Gauge(
    name="db_pool_checked_out",
    documentation="数据库连接池已使用连接数",
    registry=registry
)

# 数据库查询延迟
db_query_duration_seconds = Histogram(
    name="db_query_duration_seconds",
    documentation="数据库查询延迟(秒)",
    labelnames=["operation"],  # select/insert/update/delete
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry
)

# 缓存命中率
cache_hits_total = Counter(
    name="cache_hits_total",
    documentation="缓存命中总数",
    registry=registry
)

cache_misses_total = Counter(
    name="cache_misses_total",
    documentation="缓存未命中总数",
    registry=registry
)

# Redis连接池状态
redis_pool_size = Gauge(
    name="redis_pool_size",
    documentation="Redis连接池大小",
    registry=registry
)

# ==================== 错误指标 ====================

# 错误总数
errors_total = Counter(
    name="errors_total",
    documentation="错误总数",
    labelnames=["error_type", "endpoint"],
    registry=registry
)

# 异常总数
exceptions_total = Counter(
    name="exceptions_total",
    documentation="异常总数",
    labelnames=["exception_type"],
    registry=registry
)


class MetricsService:
    """指标服务类 - 提供便捷的指标记录方法"""
    
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
        """记录HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: 端点路径
            status: HTTP状态码
            duration: 请求耗时(秒)
        """
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_conversation_created() -> None:
        """记录会话创建"""
        conversations_total.inc()
        active_conversations.inc()
    
    @staticmethod
    def record_conversation_closed() -> None:
        """记录会话关闭"""
        active_conversations.dec()
    
    @staticmethod
    def record_message(role: str) -> None:
        """记录消息
        
        Args:
            role: 消息角色(user/assistant)
        """
        messages_total.labels(role=role).inc()
    
    @staticmethod
    def record_tool_call(tool_name: str, status: str, duration: float) -> None:
        """记录工具调用
        
        Args:
            tool_name: 工具名称
            status: 调用状态(success/error)
            duration: 调用耗时(秒)
        """
        tool_calls_total.labels(tool_name=tool_name, status=status).inc()
        tool_call_duration_seconds.labels(tool_name=tool_name).observe(duration)
    
    @staticmethod
    def record_agent_created() -> None:
        """记录Agent创建"""
        active_agents.inc()
    
    @staticmethod
    def record_agent_destroyed() -> None:
        """记录Agent销毁"""
        active_agents.dec()
    
    @staticmethod
    def record_cache_hit() -> None:
        """记录缓存命中"""
        cache_hits_total.inc()
    
    @staticmethod
    def record_cache_miss() -> None:
        """记录缓存未命中"""
        cache_misses_total.inc()
    
    @staticmethod
    def record_error(error_type: str, endpoint: str = "") -> None:
        """记录错误
        
        Args:
            error_type: 错误类型
            endpoint: 端点路径
        """
        errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
    
    @staticmethod
    def record_exception(exception_type: str) -> None:
        """记录异常
        
        Args:
            exception_type: 异常类型
        """
        exceptions_total.labels(exception_type=exception_type).inc()
    
    @staticmethod
    def record_db_query(operation: str, duration: float) -> None:
        """记录数据库查询
        
        Args:
            operation: 操作类型(select/insert/update/delete)
            duration: 查询耗时(秒)
        """
        db_query_duration_seconds.labels(operation=operation).observe(duration)


# 全局指标服务实例
metrics_service = MetricsService()


def get_metrics_service() -> MetricsService:
    """获取指标服务实例(用于依赖注入)"""
    return metrics_service
