# app/utils/validators.py
# 验证器 - 数据验证工具

import re
from typing import Optional


def validate_stock_symbol(symbol: str) -> bool:
    """验证股票代码格式
    
    Args:
        symbol: 股票代码
        
    Returns:
        是否有效
    """
    if not symbol:
        return False
    
    # 匹配SH或SZ开头,后跟6位数字
    pattern = r'^(SH|SZ)\d{6}$'
    return bool(re.match(pattern, symbol.upper()))


def validate_conversation_id(conversation_id: str) -> bool:
    """验证会话ID格式
    
    Args:
        conversation_id: 会话ID
        
    Returns:
        是否有效
    """
    if not conversation_id:
        return False
    
    # 匹配格式: YYYYMMDD-HHMMSS+5位数字
    pattern = r'^\d{8}-\d{6}\d{5}$'
    return bool(re.match(pattern, conversation_id))


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """清理输入文本
    
    Args:
        text: 输入文本
        max_length: 最大长度
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除首尾空白
    text = text.strip()
    
    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_pagination(skip: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
    """验证分页参数
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        max_limit: 最大限制
        
    Returns:
        验证后的(skip, limit)
    """
    skip = max(0, skip)
    limit = max(1, min(limit, max_limit))
    return skip, limit
