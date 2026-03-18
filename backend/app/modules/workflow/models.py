# app/modules/workflow/models.py
"""
工作流模块 - 数据模型定义

包含：
- workflows_table: 工作流定义表
- workflow_executions_table: 工作流执行记录表
- workflow_node_executions_table: 工作流节点执行记录表
- workflow_versions_table: 工作流版本历史表
"""
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from app.core.db.database import metadata


# ========== 1. 工作流定义表 ==========
workflows_table = Table(
    "workflows",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 基本信息
    Column("workflow_id", String(100), nullable=False, unique=True, description="工作流唯一标识"),
    Column("name", String(100), nullable=False, description="工作流名称"),
    Column("description", Text, description="工作流描述"),
    
    # 关联
    Column("node_id", Integer, ForeignKey("nodes.id"), nullable=False, description="所属节点ID"),
    
    # 工作流定义
    Column("schedule", String(50), description="Cron表达式（定时触发）"),
    Column("nodes", JSON, default=list, description="节点定义列表"),
    Column("edges", JSON, default=list, description="边定义列表（连线）"),
    
    # 状态
    Column("is_active", Boolean, default=True, description="是否启用"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, description="更新时间"),
    
    sqlite_autoincrement=True,
)


# ========== 2. 工作流执行记录表 ==========
workflow_executions_table = Table(
    "workflow_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 关联
    Column("workflow_id", String(100), ForeignKey("workflows.workflow_id"), nullable=False, description="工作流ID"),
    
    # 执行信息
    Column("status", String(20), default="pending", description="状态：pending/running/success/failed/cancelled"),
    Column("triggered_by", String(20), default="system", description="触发方式：manual/system/schedule"),
    
    # 执行时间
    Column("start_time", DateTime, default=datetime.now, description="开始时间"),
    Column("end_time", DateTime, description="结束时间"),
    
    # 结果
    Column("error", Text, description="错误信息"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    
    sqlite_autoincrement=True,
)


# ========== 3. 工作流节点执行记录表 ==========
workflow_node_executions_table = Table(
    "workflow_node_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 关联
    Column("execution_id", Integer, ForeignKey("workflow_executions.id"), nullable=False, description="执行记录ID"),
    
    # 节点信息
    Column("node_id", String(100), nullable=False, description="节点ID（工作流内）"),
    Column("node_name", String(100), description="节点名称"),
    Column("node_type", String(20), description="节点类型"),
    
    # 执行状态
    Column("status", String(20), default="pending", description="状态：pending/running/success/failed/skipped"),
    
    # 执行时间
    Column("start_time", DateTime, description="开始时间"),
    Column("end_time", DateTime, description="结束时间"),
    
    # 结果
    Column("output", Text, description="输出"),
    Column("error", Text, description="错误信息"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    
    sqlite_autoincrement=True,
)


# ========== 4. 工作流版本历史表 ==========
workflow_versions_table = Table(
    "workflow_versions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 关联
    Column("workflow_id", String(100), ForeignKey("workflows.workflow_id"), nullable=False, description="工作流ID"),
    
    # 版本信息
    Column("version", Integer, nullable=False, description="版本号"),
    Column("name", String(100), nullable=False, description="版本名称"),
    Column("description", Text, description="版本描述"),
    
    # 快照
    Column("nodes", JSON, default=list, description="节点定义快照"),
    Column("edges", JSON, default=list, description="边定义快照"),
    
    # 变更信息
    Column("change_note", Text, description="变更说明"),
    Column("created_by", String(100), description="创建者"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    
    sqlite_autoincrement=True,
)


__all__ = [
    "workflows_table",
    "workflow_executions_table",
    "workflow_node_executions_table",
    "workflow_versions_table"
]
