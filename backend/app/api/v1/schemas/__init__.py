# app/api/v1/schemas/__init__.py
# API schemas导出

from app.api.v1.schemas.chat import ChatRequest, ChatChunkResponse
from app.api.v1.schemas.conversation import (
    MessageSchema,
    ConversationSummary,
    ConversationDetail,
    ConversationsResponse,
    CreateConversationRequest,
    UpdateConversationRequest
)

__all__ = [
    "ChatRequest",
    "ChatChunkResponse",
    "MessageSchema",
    "ConversationSummary",
    "ConversationDetail",
    "ConversationsResponse",
    "CreateConversationRequest",
    "UpdateConversationRequest",
]
