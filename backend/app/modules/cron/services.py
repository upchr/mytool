from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.engine import Engine
from datetime import datetime
import threading
from . import models, schemas
from .ssh_client import SSHClient
from app.modules.cron.schemas import JobExecutionRead

# 节点管理
def create_node(engine: Engine, node: schemas.NodeCreate) -> dict:
    stmt = insert(models.nodes_table).values(**node.model_dump())
    with engine.begin() as conn:
        result = conn.execute(stmt)


def get_nodes(engine: Engine, active_only: bool = True) -> list[dict]:
    stmt = select(models.nodes_table)
    if active_only:
        stmt = stmt.where(models.nodes_table.c.is_active == True)
    with engine.connect() as conn:
        result = conn.execute(stmt)
        return [dict(row) for row in result.mappings()]

def get_node(engine: Engine, node_id: int) -> dict:
    stmt = select(models.nodes_table).where(models.nodes_table.c.id == node_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        return dict(result) if result else None

# 任务管理
def create_cron_job(engine: Engine, job: schemas.CronJobCreate) -> dict:
    stmt = insert(models.cron_jobs_table).values(**job.model_dump())
    with engine.begin() as conn:
        result = conn.execute(stmt)
        job_id = result.inserted_primary_key[0]
        return get_cron_job(engine, job_id)

def get_cron_jobs(engine: Engine, node_id: int = None) -> list[dict]:
    stmt = select(models.cron_jobs_table)
    if node_id:
        stmt = stmt.where(models.cron_jobs_table.c.node_id == node_id)
    with engine.connect() as conn:
        result = conn.execute(stmt)
        return [dict(row) for row in result.mappings()]

# 执行任务
def execute_job(engine: Engine, job_id: int, triggered_by: str = "manual") -> schemas.JobExecutionRead:
    # 创建执行记录
    stmt = insert(models.job_executions_table).values(
        job_id=job_id,
        start_time=datetime.utcnow(),
        status="running",
        triggered_by=triggered_by
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        execution_id = result.inserted_primary_key[0]

        # 获取任务详情
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()

        # 获取节点信息
        node_stmt = select(models.nodes_table).where(models.nodes_table.c.id == job['node_id'])
        node = conn.execute(node_stmt).mappings().first()

    # 异步执行
    def run_task():
        ssh = SSHClient(schemas.NodeRead(**node))
        try:
            ssh.connect()
            exit_code, output, error = ssh.execute_command(job['command'])
            status = "success" if exit_code == 0 else "failed"
        except Exception as e:
            exit_code, output, error = 1, "", str(e)
            status = "failed"
        finally:
            ssh.close()

        # 更新执行记录
        update_stmt = (
            update(models.job_executions_table)
            .where(models.job_executions_table.c.id == execution_id)
            .values(
                end_time=datetime.utcnow(),
                status=status,
                output=output[:1000],  # 限制日志长度
                error=error[:1000]
            )
        )
        with engine.begin() as conn:
            conn.execute(update_stmt)

    threading.Thread(target=run_task, daemon=True).start()
    return get_execution(engine, execution_id)

# 获取执行记录
def get_executions(engine: Engine, job_id: int, limit: int = 10) -> list[dict]:
    stmt = (
        select(models.job_executions_table)
        .where(models.job_executions_table.c.job_id == job_id)
        .order_by(models.job_executions_table.c.start_time.desc())
        .limit(limit)
    )
    with engine.connect() as conn:
        result = conn.execute(stmt)
        return [dict(row) for row in result.mappings()]

def get_execution(engine: Engine, execution_id: int) -> dict:
    stmt = select(models.job_executions_table).where(models.job_executions_table.c.id == execution_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        return dict(result) if result else None

# 批量执行
def execute_jobs(engine: Engine, request: schemas.ManualExecutionRequest) -> list[dict]:
    results = []
    for job_id in request.job_ids:
        execution = execute_job(engine, job_id, "manual")
        results.append(execution)
    return results
