# app/models/base.py
# 数据库模型基类

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class TimestampMixin:
    """时间戳混入类 - 自动管理创建和更新时间"""
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
            comment="创建时间"
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
            comment="更新时间"
        )


class BaseModel(Base, TimestampMixin):
    """抽象基础模型类"""
    
    __abstract__ = True
    
    def to_dict(self):
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
