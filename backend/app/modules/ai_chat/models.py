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

# 知识库表
knowledge_base_table = Table(
    "ai_knowledge_base",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, comment="知识库名称"),
    Column("description", Text, nullable=True, comment="知识库描述"),
    Column("is_active", Boolean, default=True, comment="是否启用"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

# 知识文档表
knowledge_document_table = Table(
    "ai_knowledge_document",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("knowledge_base_id", Integer, ForeignKey("ai_knowledge_base.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(255), nullable=False, comment="文档标题"),
    Column("content", Text, nullable=False, comment="文档内容"),
    Column("category", String(100), nullable=True, comment="文档分类"),
    Column("tags", String(500), nullable=True, comment="文档标签，逗号分隔"),
    Column("is_active", Boolean, default=True, comment="是否启用"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

# 知识分片表（用于向量检索）
knowledge_chunk_table = Table(
    "ai_knowledge_chunk",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", Integer, ForeignKey("ai_knowledge_document.id", ondelete="CASCADE"), nullable=False),
    Column("chunk_index", Integer, nullable=False, comment="分片索引"),
    Column("content", Text, nullable=False, comment="分片内容"),
    Column("metadata", Text, nullable=True, comment="元数据，JSON格式"),
    Column("created_at", DateTime, nullable=False),
    sqlite_autoincrement=True,
)

__all__ = [
    "conversations_table",
    "messages_table",
    "ai_config_table",
    "knowledge_base_table",
    "knowledge_document_table",
    "knowledge_chunk_table"
]