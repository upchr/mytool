from sqlalchemy import Table, Column, Integer, String, Text,Boolean
from app.core.db.database import metadata, engine

# 从节点信息表
nodes_table = Table(
    "nodes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(50), unique=True, nullable=False),
    Column("host", String(255), nullable=False),
    Column("port", Integer, default=22),
    Column("username", String(50), nullable=False),
    Column("auth_type", String(10), default="password"),  # password/ssh_key
    Column("password", Text),
    Column("private_key", Text),
    Column("is_active", Boolean, default=True),
    sqlite_autoincrement=True,

)
credential_templates_table = Table(
    "credential_templates",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), unique=True, nullable=False),  # 模板名称，如 "root@prod"
    Column("username", String(100), nullable=False),
    Column("auth_type", String(10), nullable=False),  # 'password' or 'ssh_key'
    Column("password", String(255)),   # 可加密存储（建议）
    Column("private_key", Text),       # PEM 格式
    Column("is_active", Boolean, default=True),
    sqlite_autoincrement=True,
)

__all__ = ["nodes_table","credential_templates_table"]
