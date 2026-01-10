# app/core/config.py
# 配置管理系统 - 使用Pydantic Settings实现类型安全的配置管理

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """应用配置类
    
    支持从环境变量和.env文件加载配置
    """
    
    # 应用基础配置
    APP_NAME: str = "股票分析智能体API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="运行环境: development/production")
    DEBUG: bool = Field(default=True, description="调试模式")
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = Field(default="0.0.0.0", description="API服务地址")
    API_PORT: int = Field(default=8000, description="API服务端口")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        description="允许的跨域来源"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://admin:password@localhost:5432/stock_analysis",
        description="数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="数据库连接池最大溢出")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="数据库连接超时(秒)")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="数据库连接回收时间(秒)")
    
    # Redis缓存配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis连接池大小")
    CACHE_TTL: int = Field(default=300, description="缓存过期时间(秒)")
    
    # 豆包API配置
    DOUBAO_API_KEY: str = Field(default="", description="豆包API密钥")
    DOUBAO_BASE_URL: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        description="豆包API基础URL"
    )
    DOUBAO_MODEL: str = Field(
        default="doubao-seed-1-6-251015",
        description="豆包模型名称"
    )
    
    # 雪球API配置
    XQ_A_TOKEN: str = Field(default="", description="雪球API Token")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_DIR: str = Field(default="logs", description="日志目录")
    LOG_ROTATION: str = Field(default="00:00", description="日志轮转时间")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")
    LOG_FORMAT: str = Field(default="json", description="日志格式: json/text")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用Prometheus指标")
    METRICS_PORT: int = Field(default=9090, description="指标服务端口")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="启用限流")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    
    # 文件存储配置
    FILES_DIR: str = Field(default="files", description="文件存储目录")
    ENABLE_FILE_BACKUP: bool = Field(default=True, description="启用文件备份")
    
    # 性能配置
    REQUEST_TIMEOUT: int = Field(default=300, description="请求超时时间(秒)")
    MAX_CONNECTIONS: int = Field(default=100, description="最大并发连接数")
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境配置"""
        allowed = ["development", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT必须是以下之一: {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL必须是以下之一: {allowed}")
        return v_upper
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库URL(用于Alembic)"""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例(用于依赖注入)"""
    return settings
