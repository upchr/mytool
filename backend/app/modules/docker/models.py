from sqlalchemy import Table, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from app.core.db.database import metadata


docker_operation_logs_table = Table(
    "docker_operation_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    Column("node_id", Integer, ForeignKey("nodes.id"), nullable=False, comment="节点ID"),
    Column("operation_type", String(50), nullable=False, comment="操作类型：container/compose/image等"),
    Column("action", String(50), nullable=False, comment="具体操作：start/stop/up/down等"),
    Column("target", String(500), comment="操作目标：容器ID/项目路径等"),
    Column("status", String(20), nullable=False, comment="操作状态：success/failed"),
    Column("message", Text, comment="操作结果消息"),

    Column("created_at", DateTime, nullable=False, comment="创建时间"),

    sqlite_autoincrement=True,
)


docker_favorite_containers_table = Table(
    "docker_favorite_containers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    Column("node_id", Integer, ForeignKey("nodes.id"), nullable=False, comment="节点ID"),
    Column("container_id", String(100), nullable=False, comment="容器ID"),
    Column("container_name", String(200), comment="容器名称"),
    Column("alias", String(100), comment="别名"),
    Column("sort_order", Integer, default=0, comment="排序"),

    Column("created_at", DateTime, nullable=False, comment="创建时间"),
    Column("updated_at", DateTime, nullable=False, comment="更新时间"),

    sqlite_autoincrement=True,
)


__all__ = ["docker_operation_logs_table", "docker_favorite_containers_table"]
