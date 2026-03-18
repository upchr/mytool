from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from app.core.db.database import engine, metadata
from datetime import datetime

# 工作流表
workflows_table = Table(
    "workflows",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_id", String(100), nullable=False, unique=True),  # 工作流唯一标识
    Column("name", String(100), nullable=False),  # 工作流名称
    Column("description", Text),  # 描述
    Column("node_id", Integer, ForeignKey("nodes.id"), nullable=False),  # 所属节点
    Column("schedule", String(50)),  # Cron表达式（定时触发）
    Column("nodes", JSON, default=list),  # 节点定义
    Column("edges", JSON, default=list),  # 边定义（连线）
    Column("is_active", Boolean, default=True),  # 是否启用
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 工作流执行记录表
workflow_executions_table = Table(
    "workflow_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_id", String(100), ForeignKey("workflows.workflow_id"), nullable=False),
    Column("status", String(20), default="pending"),  # pending/running/success/failed/cancelled
    Column("start_time", DateTime, nullable=False, default=datetime.utcnow),
    Column("end_time", DateTime),
    Column("triggered_by", String(20), default="system"),  # manual/system
    Column("error", Text),  # 错误信息
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 工作流节点执行记录表
workflow_node_executions_table = Table(
    "workflow_node_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("execution_id", Integer, ForeignKey("workflow_executions.id"), nullable=False),
    Column("node_id", String(100), nullable=False),  # 工作流内的节点ID
    Column("node_name", String(100)),  # 节点名称
    Column("status", String(20), default="pending"),  # pending/running/success/failed/skipped
    Column("start_time", DateTime),
    Column("end_time", DateTime),
    Column("output", Text),  # 输出
    Column("error", Text),  # 错误
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

__all__ = [
    "workflows_table",
    "workflow_executions_table",
    "workflow_node_executions_table"
]
