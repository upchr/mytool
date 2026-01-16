from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from app.core.database import metadata

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
    Column("password", String(255)),
    Column("private_key", Text),
    Column("is_active", Boolean, default=True),
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
    Column("is_active", Boolean, default=True)
)
# 定时任务表
cron_jobs_table = Table(
    "cron_jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_id", Integer, ForeignKey("nodes.id"), nullable=False),
    Column("name", String(100), nullable=False),
    Column("schedule", String(50), nullable=False),  # crontab format
    Column("command", Text, nullable=False),
    Column("description", Text),
    Column("is_active", Boolean, default=True),
)

# 任务执行日志表
job_executions_table = Table(
    "job_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Integer, ForeignKey("cron_jobs.id"), nullable=False),
    Column("start_time", DateTime, nullable=False),
    Column("end_time", DateTime),
    Column("status", String(20), default="pending"), # pending/running/success/failed
    Column("output", Text),
    Column("error", Text),
    Column("triggered_by", String(20)), # manual/system
)
