# app/api/v1/routes/__init__.py
# API v1路由导出

from fastapi import APIRouter

from app.api.v1.routes import chat, conversations, health

# 创建v1路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(health.router)

__all__ = ["api_router"]
