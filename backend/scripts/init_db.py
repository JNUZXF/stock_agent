# scripts/init_db.py
# 数据库初始化脚本

import sys
import asyncio
from pathlib import Path
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import get_engine, Base
from app.core.config import settings
from app.models import Conversation, Message

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_database():
    """初始化数据库"""
    logger.info("=" * 80)
    logger.info("数据库初始化")
    logger.info(f"环境: {settings.ENVIRONMENT}")
    logger.info(f"数据库: {settings.DATABASE_URL.split('@')[-1]}")
    logger.info("=" * 80)
    
    try:
        # 获取引擎
        engine = get_engine()
        
        # 创建所有表
        logger.info("创建数据库表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建成功")
        
        # 列出创建的表
        logger.info("已创建的表:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
        
        # 关闭引擎
        await engine.dispose()
        
        logger.info("=" * 80)
        logger.info("数据库初始化完成")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())
