# app/models/conversation.py
# 会话数据模型

from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Conversation(BaseModel):
    """会话模型
    
    存储用户会话的基本信息和元数据
    """
    
    __tablename__ = "conversations"
    
    id = Column(
        String(50),
        primary_key=True,
        comment="会话ID(格式: YYYYMMDD-HHMMSS+随机数)"
    )
    
    title = Column(
        String(200),
        nullable=False,
        default="新会话",
        comment="会话标题(通常是第一条用户消息)"
    )
    
    summary = Column(
        Text,
        nullable=True,
        comment="会话摘要"
    )
    
    metadata = Column(
        JSON,
        nullable=True,
        comment="会话元数据(JSON格式)"
    )
    
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"
