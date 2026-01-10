# scripts/migrate_files_to_db.py
# 数据迁移脚本 - 将files目录下的会话数据迁移到PostgreSQL

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_engine, Base
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_conversation(session: AsyncSession, conversation_dir: Path) -> bool:
    """迁移单个会话
    
    Args:
        session: 数据库会话
        conversation_dir: 会话目录路径
        
    Returns:
        是否迁移成功
    """
    conversation_id = conversation_dir.name
    json_file = conversation_dir / "conversation.json"
    
    if not json_file.exists():
        logger.warning(f"跳过 {conversation_id}: conversation.json不存在")
        return False
    
    try:
        # 读取会话数据
        with open(json_file, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
        
        if not messages_data:
            logger.warning(f"跳过 {conversation_id}: 没有消息")
            return False
        
        # 提取标题(第一条用户消息)
        title = "新会话"
        for msg in messages_data:
            if msg.get("role") == "user" and "content" in msg:
                content = msg["content"]
                title = content[:50] + ("..." if len(content) > 50 else "")
                break
        
        # 提取摘要(最后一条助手消息)
        summary = None
        for msg in reversed(messages_data):
            if msg.get("role") == "assistant" and "content" in msg:
                content = msg["content"]
                summary = content[:200] + ("..." if len(content) > 200 else "")
                break
        
        # 检查会话是否已存在
        existing = await session.get(Conversation, conversation_id)
        if existing:
            logger.info(f"跳过 {conversation_id}: 已存在")
            return False
        
        # 创建会话记录
        conversation = Conversation(
            id=conversation_id,
            title=title,
            summary=summary
        )
        session.add(conversation)
        
        # 创建消息记录
        message_count = 0
        for msg_data in messages_data:
            role = msg_data.get("role")
            content = msg_data.get("content")
            
            # 跳过system消息和function_call相关消息(如果没有content)
            if role in ["user", "assistant"] and content:
                message = Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    message_type=msg_data.get("type", "message"),
                    metadata=json.dumps(msg_data) if msg_data else None
                )
                session.add(message)
                message_count += 1
        
        # 提交事务
        await session.commit()
        
        logger.info(f"迁移成功: {conversation_id} ({message_count}条消息)")
        return True
        
    except Exception as e:
        logger.error(f"迁移失败 {conversation_id}: {e}", exc_info=True)
        await session.rollback()
        return False


async def migrate_all():
    """迁移所有会话"""
    logger.info("=" * 80)
    logger.info("开始数据迁移")
    logger.info(f"环境: {settings.ENVIRONMENT}")
    logger.info(f"数据库: {settings.DATABASE_URL.split('@')[-1]}")
    logger.info("=" * 80)
    
    # 获取files目录
    files_dir = Path(settings.FILES_DIR)
    if not files_dir.exists():
        logger.error(f"files目录不存在: {files_dir}")
        return
    
    # 获取所有会话目录
    conversation_dirs = [
        d for d in files_dir.iterdir()
        if d.is_dir() and (d / "conversation.json").exists()
    ]
    
    logger.info(f"找到 {len(conversation_dirs)} 个会话")
    
    if not conversation_dirs:
        logger.info("没有需要迁移的数据")
        return
    
    # 创建数据库引擎
    engine = get_engine()
    
    # 创建所有表
    logger.info("创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表创建完成")
    
    # 迁移数据
    success_count = 0
    fail_count = 0
    
    from sqlalchemy.ext.asyncio import async_sessionmaker
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    for conv_dir in conversation_dirs:
        async with async_session() as session:
            if await migrate_conversation(session, conv_dir):
                success_count += 1
            else:
                fail_count += 1
    
    # 关闭引擎
    await engine.dispose()
    
    # 输出统计
    logger.info("=" * 80)
    logger.info("迁移完成")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败/跳过: {fail_count}")
    logger.info(f"总计: {len(conversation_dirs)}")
    logger.info("=" * 80)
    
    # 备份提示
    if success_count > 0:
        logger.info(f"提示: 原文件保留在 {files_dir} 目录,建议备份后再删除")


if __name__ == "__main__":
    asyncio.run(migrate_all())
