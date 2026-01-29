from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from app.core.db.database import engine,metadata

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

if __name__ != "__main__":
    metadata.create_all(engine, tables=[
        cron_jobs_table,
        job_executions_table,
    ])
