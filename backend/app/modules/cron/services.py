from croniter import croniter
from sqlalchemy import select, insert, update, delete, desc, Engine
from datetime import datetime
import threading

from app.core.sh.ssh_client import SSHClient

from . import models, schemas
from .scheduler import scheduler
from app.core.ws.ws_manager import ws_manager
from app.core.interrupt.execution_manager import execution_manager, ExecutionCancelledError

from app.modules.node.models import nodes_table


# 任务管理
def create_cron_job(engine: Engine, job: schemas.CronJobCreate) -> dict:
    data = job.model_dump()
    stmt = insert(models.cron_jobs_table).values(**data)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        job_id = result.inserted_primary_key[0]
        return {"id": job_id, **data}

def get_cron_jobs(engine: Engine, node_ids: list[int] = None) -> list[dict]:
    stmt = (
        select(models.cron_jobs_table)
        .join(
            nodes_table,
            models.cron_jobs_table.c.node_id == nodes_table.c.id
        )
        .where(nodes_table.c.is_active.is_(True))
        .order_by(models.cron_jobs_table.c.name, nodes_table.c.name)
    )

    # 多节点筛选
    if node_ids and len(node_ids) > 0:
        stmt = stmt.where(models.cron_jobs_table.c.node_id.in_(node_ids))
    with engine.connect() as conn:
        result = conn.execute(stmt)
        jobs = []
        for row in result.mappings():
            job_dict = dict(row)

            # 计算下次执行时间
            try:
                if job_dict['is_active']:
                    cron = croniter(job_dict['schedule'], datetime.now())
                    next_run = cron.get_next(datetime)
                    job_dict['next_run'] = next_run.isoformat()
                else:
                    job_dict['next_run'] = None
            except Exception:
                job_dict['next_run'] = None

            jobs.append(job_dict)
        return jobs

def execute_job(engine: Engine, job_id: int, triggered_by: str = "manual") -> dict:
    """执行任务并实时保存日志"""
    # 获取任务和节点（提前验证）
    with engine.connect() as conn:
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            scheduler.remove_job(job_id, '该任务不存在')
            raise ValueError(f"任务 {job_id} 不存在，已移除计划")

        node_stmt = select(nodes_table).where(nodes_table.c.id == job['node_id'])
        node = conn.execute(node_stmt).mappings().first()
        if not node:
            scheduler.remove_job(job_id, f"任务 {job_id} 的节点{job['node_id']}不存在")
            raise ValueError(f"任务 {job_id} 的节点{job['node_id']}不存在，已移除计划")

    # 创建执行记录
    stmt = insert(models.job_executions_table).values(
        job_id=job_id,
        start_time=datetime.now(),
        status="running",
        triggered_by=triggered_by
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        execution_id = result.inserted_primary_key[0]
        print(f"✅ 任务调度：时间（{datetime.now().replace(second=0, microsecond=0)}），设备（{node['name']}），任务（{job['name']}），触发方式（{triggered_by}）")

    def run_task():
        ssh = None
        output_buffer = []  # 当前未保存的输出片段
        error_buffer = []   # 当前未保存的错误片段
        out_len = 2000 #追加入库分片长度
        error_len = 1000
        try:
            # 创建停止事件
            execution_manager.create_execution(execution_id)
            # 初始化数据库记录（空日志）
            _init_execution_log(engine, execution_id)

            from app.modules.node.schemas import NodeRead
            ssh = SSHClient(NodeRead(**node))
            ssh.connect()

            initial_log = {"status": "running", "output": "正在连接...\n", "error": "", "end_time": None}
            ws_manager.send_log_sync(execution_id, initial_log)

            _, stdout, stderr = ssh.client.exec_command(job['command'], timeout=60)

            while True:
                # 检查是否需要中断
                if execution_manager.should_stop(execution_id):
                    raise ExecutionCancelledError("任务已被用户中断")

                # 处理 stdout
                if stdout.channel.recv_ready():
                    line = stdout.channel.recv(1024).decode('utf-8', errors='replace')
                    if line:
                        output_buffer.append(line)
                        # 实时推送到 WebSocket
                        log_data = {
                            "status": "running",
                            "output": line,
                            "error": "",
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)

                        # 检查是否需要保存到数据库
                        if len("".join(output_buffer)) >= out_len:
                            _save_and_clear_buffer(engine, execution_id, output_buffer, [], "running")

                # 处理 stderr
                if stderr.channel.recv_stderr_ready():
                    line = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
                    if line:
                        error_buffer.append(line)
                        # 实时推送到 WebSocket
                        log_data = {
                            "status": "running",
                            "output": "",
                            "error": line,
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)

                        # 检查是否需要保存到数据库
                        if len("".join(error_buffer)) >= error_len:
                            _save_and_clear_buffer(engine, execution_id, [], error_buffer, "running")

                if stdout.channel.exit_status_ready():
                    # stdout 兜底
                    while stdout.channel.recv_ready():
                        line = stdout.channel.recv(4096).decode("utf-8", errors="replace")
                        if line:
                            output_buffer.append(line)
                            log_data = {"status": "running", "output": line, "error": "", "end_time": None}
                            ws_manager.send_log_sync(execution_id, log_data)

                    # stderr 兜底
                    while stderr.channel.recv_stderr_ready():
                        line = stderr.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                        if line:
                            error_buffer.append(line)
                            log_data = {"status": "running", "output": "", "error": line, "end_time": None}
                            ws_manager.send_log_sync(execution_id, log_data)

                    break

            # 保存剩余日志
            if output_buffer:
                _save_and_clear_buffer(engine, execution_id, output_buffer, [], "running")
            if error_buffer:
                _save_and_clear_buffer(engine, execution_id, [], error_buffer, "running")

            exit_code = stdout.channel.recv_exit_status()
            status = "success" if exit_code == 0 else "failed"

            # 更新最终状态
            _update_execution_final_status(engine, execution_id, status)

            final_output = "".join(output_buffer)  # 此时 buffer 已清空，但我们需要最终内容用于 WebSocket
            final_error = "".join(error_buffer)

            final_log = {
                "status": status,
                "output": final_output,
                "error": final_error,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)

        except ExecutionCancelledError as e:
            error_msg = str(e)
            # 保存剩余输出日志
            if output_buffer:
                _save_and_clear_buffer(engine, execution_id, output_buffer, [], "cancelled")
            # 保存错误信息
            if error_msg:
                _save_and_clear_buffer(engine, execution_id, [], [error_msg], "cancelled")

            _update_execution_final_status(engine, execution_id, "cancelled")

            final_output = "".join(output_buffer) if 'output_buffer' in locals() else ""
            final_error = error_msg

            final_log = {
                "status": "cancelled",
                "output": final_output,
                "error": final_error,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)

        except Exception as e:
            error_msg = str(e)
            # 保存错误信息
            _save_and_clear_buffer(engine, execution_id, [], [error_msg], "failed")
            _update_execution_final_status(engine, execution_id, "failed")

            final_log = {
                "status": "failed",
                "output": "",
                "error": error_msg,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)

        finally:
            if ssh:
                ssh.close()
            # 清理资源
            execution_manager.cleanup(execution_id)
            ws_manager.cleanup(execution_id)

    threading.Thread(target=run_task, daemon=True).start()
    return get_execution(engine, execution_id)
def _init_execution_log(engine: Engine, execution_id: int):
    """初始化执行日志记录（空内容）"""
    stmt = (
        update(models.job_executions_table)
        .where(models.job_executions_table.c.id == execution_id)
        .values(
            output="",
            error="",
            status="running",
            end_time=None
        )
    )
    with engine.begin() as conn:
        conn.execute(stmt)
def _save_and_clear_buffer(engine: Engine, execution_id: int, output_buffer: list, error_buffer: list, status: str):
    """保存缓冲区内容并清空"""
    if not output_buffer and not error_buffer:
        return

    output_str = "".join(output_buffer)
    error_str = "".join(error_buffer)

    # 追加到数据库
    stmt = (
        update(models.job_executions_table)
        .where(models.job_executions_table.c.id == execution_id)
        .values(
            output=models.job_executions_table.c.output + output_str,
            error=models.job_executions_table.c.error + error_str,
            status=status,
            end_time=datetime.now() if status in ["success", "failed", "cancelled"] else None
        )
    )
    with engine.begin() as conn:
        conn.execute(stmt)

    # 👇 关键：清空缓冲区
    output_buffer.clear()
    error_buffer.clear()
def _update_execution_final_status(engine: Engine, execution_id: int, status: str):
    """更新最终状态和结束时间"""
    stmt = (
        update(models.job_executions_table)
        .where(models.job_executions_table.c.id == execution_id)
        .values(
            status=status,
            end_time=datetime.now()
        )
    )
    with engine.begin() as conn:
        conn.execute(stmt)

def update_cron_job(engine, job_id: int, update_data: dict) -> bool:
    with engine.connect() as conn:
        stmt = (
            update(models.cron_jobs_table)
            .where(models.cron_jobs_table.c.id == job_id)
            .values(**update_data)
        )
        result = conn.execute(stmt)
        conn.commit()
        return result.rowcount > 0
def get_cron_job(engine, job_id: int):
    with engine.connect() as conn:
        query = models.cron_jobs_table.select().where(models.cron_jobs_table.c.id == job_id)
        result = conn.execute(query).fetchone()
        return result._asdict() if result else None

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

def toggle_job_status(engine: Engine, job_id: int, is_active: bool) -> bool:
    stmt = (
        update(models.cron_jobs_table)
        .where(models.cron_jobs_table.c.id == job_id)
        .values(is_active=is_active)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            return False

        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            return False

        if is_active:
            scheduler.add_job(job)
        else:
            scheduler.remove_job(job_id, job['name'])
        return True

def remove_job(engine: Engine, job_id: int) -> bool:
    with engine.begin() as conn:
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            return False

        stmt = delete(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        result = conn.execute(stmt)
        scheduler.remove_job(job_id, job['name'])
        return result.rowcount > 0

def get_next_crons(cron: schemas.CronReq) -> list[dict]:
    cron = croniter(cron.cron, datetime.now())
    # 获取最近的5次执行时间
    recent_runs = []
    for _ in range(5):
        next_run = cron.get_next(datetime)
        recent_runs.append(schemas.CronNextRes(next_run=next_run.isoformat()))
    return recent_runs
