# app/core/logging.py
# 生产级日志系统 - 结构化、分级、异步、安全

import logging
import logging.handlers
import sys
import json
import re
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

from app.core.config import settings


# 上下文变量用于存储请求级别的追踪信息
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器 - 自动脱敏密码、token等敏感信息"""
    
    SENSITIVE_PATTERNS = [
        (re.compile(r'("password"\s*:\s*)"[^"]*"'), r'\1"***REDACTED***"'),
        (re.compile(r'("token"\s*:\s*)"[^"]*"'), r'\1"***REDACTED***"'),
        (re.compile(r'("api_key"\s*:\s*)"[^"]*"'), r'\1"***REDACTED***"'),
        (re.compile(r'("secret"\s*:\s*)"[^"]*"'), r'\1"***REDACTED***"'),
        (re.compile(r'("authorization"\s*:\s*)"[^"]*"'), r'\1"***REDACTED***"'),
        (re.compile(r'(password=)[^\s&]+'), r'\1***REDACTED***'),
        (re.compile(r'(token=)[^\s&]+'), r'\1***REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感信息"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


class ContextJsonFormatter(jsonlogger.JsonFormatter):
    """自定义JSON格式化器 - 添加上下文信息"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """添加自定义字段到日志记录"""
        super().add_fields(log_record, record, message_dict)
        
        # 添加时间戳
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # 添加日志级别
        log_record['level'] = record.levelname
        
        # 添加模块信息
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # 添加进程和线程信息
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # 添加请求追踪信息
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_record['user_id'] = user_id
        
        # 添加环境信息
        log_record['environment'] = settings.ENVIRONMENT


class TextFormatter(logging.Formatter):
    """文本格式化器 - 用于开发环境"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 添加颜色(仅在终端输出时)
        colors = {
            'DEBUG': '\033[36m',    # 青色
            'INFO': '\033[32m',     # 绿色
            'WARNING': '\033[33m',  # 黄色
            'ERROR': '\033[31m',    # 红色
            'CRITICAL': '\033[35m', # 紫色
        }
        reset = '\033[0m'
        
        level_color = colors.get(record.levelname, '')
        
        # 格式化基础信息
        formatted = f"{level_color}[{record.levelname}]{reset} "
        formatted += f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} "
        formatted += f"{record.name}:{record.lineno} "
        
        # 添加请求ID
        request_id = request_id_var.get()
        if request_id:
            formatted += f"[req:{request_id[:8]}] "
        
        # 添加消息
        formatted += f"- {record.getMessage()}"
        
        # 添加异常信息
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


def setup_logging() -> None:
    """配置日志系统"""
    
    # 创建日志目录
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "app").mkdir(exist_ok=True)
    (log_dir / "error").mkdir(exist_ok=True)
    (log_dir / "access").mkdir(exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 选择格式化器
    if settings.LOG_FORMAT == "json":
        formatter = ContextJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = TextFormatter()
    
    # 1. 控制台处理器(用于开发环境)
    if settings.is_development:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(TextFormatter())  # 控制台始终使用文本格式
        console_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(console_handler)
    
    # 2. 应用日志文件处理器(所有日志)
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "app" / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(app_handler)
    
    # 3. 错误日志文件处理器(仅ERROR及以上)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "error" / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(error_handler)
    
    # 4. 访问日志处理器(用于API请求日志)
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # 不传播到根日志记录器
    
    access_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "access" / "access.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    access_logger.addHandler(access_handler)
    
    # 配置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    
    # 记录日志系统初始化完成
    root_logger.info(
        "日志系统初始化完成",
        extra={
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "environment": settings.ENVIRONMENT
        }
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称(通常使用模块名)
    
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)


def set_request_context(request_id: str, user_id: str = "") -> None:
    """设置请求上下文信息
    
    Args:
        request_id: 请求追踪ID
        user_id: 用户ID(可选)
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """清除请求上下文信息"""
    request_id_var.set("")
    user_id_var.set("")
