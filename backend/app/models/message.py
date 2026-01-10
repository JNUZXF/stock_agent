# app/models/message.py
# 消息数据模型

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Message(BaseModel):
    """消息模型
    
    存储会话中的每条消息
    """
    
    __tablename__ = "messages"
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="消息ID"
    )
    
    conversation_id = Column(
        String(50),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属会话ID"
    )
    
    role = Column(
        String(20),
        nullable=False,
        comment="消息角色: user/assistant/system/function_call_output"
    )
    
    content = Column(
        Text,
        nullable=True,
        comment="消息内容"
    )
    
    message_type = Column(
        String(50),
        nullable=True,
        default="message",
        comment="消息类型: message/function_call/function_call_output"
    )
    
    metadata = Column(
        Text,
        nullable=True,
        comment="消息元数据(JSON字符串)"
    )
    
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
    
    __table_args__ = (
        Index("idx_conversation_created", "conversation_id", "created_at"),
    )
    
    def __repr__(self):
        content_preview = self.content[:50] if self.content else ""
        return f"<Message(id={self.id}, role={self.role}, content={content_preview}...)>"
