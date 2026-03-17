# app/modules/ai_chat/models.py
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, MetaData, Boolean
from app.core.db.database import metadata, engine

conversations_table = Table(
    "ai_conversations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(255), nullable=False, default="新对话"),
    Column("user_id", Integer, nullable=True, comment="用户ID，预留字段"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

messages_table = Table(
    "ai_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Integer, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(50), nullable=False, comment="消息角色：user 或 assistant"),
    Column("content", Text, nullable=False, comment="消息内容"),
    Column("created_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

ai_config_table = Table(
    "ai_config",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, default="新配置", comment="配置名称"),
    Column("api_key", Text, nullable=True, comment="API Key"),
    Column("api_base", String(255), nullable=True, comment="API Base URL"),
    Column("model", String(100), nullable=True, comment="模型名称"),
    Column("is_enabled", Boolean, default=True, comment="是否启用"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

__all__ = ["conversations_table", "messages_table", "ai_config_table"]