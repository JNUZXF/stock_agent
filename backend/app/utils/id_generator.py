# app/utils/id_generator.py
# ID生成器 - 生成各种类型的唯一标识符

import random
import uuid
from datetime import datetime


def generate_conversation_id() -> str:
    """生成会话ID
    
    格式: YYYYMMDD-HHMMSS+5位随机数
    例如: 20240115-143052123 45
    
    Returns:
        会话ID字符串
    """
    now = datetime.now()
    time_part = now.strftime("%Y%m%d-%H%M%S")
    random_part = random.randint(10000, 99999)
    return f"{time_part}{random_part}"


def generate_request_id() -> str:
    """生成请求ID
    
    使用UUID4生成唯一请求ID
    
    Returns:
        请求ID字符串
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """生成短ID
    
    生成指定长度的随机字符串ID
    
    Args:
        length: ID长度
        
    Returns:
        短ID字符串
    """
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
