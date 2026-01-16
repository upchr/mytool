import asyncio

from croniter import croniter
from sqlalchemy import select, insert, update, delete
from sqlalchemy.engine import Engine
from datetime import datetime
import threading
from . import models, schemas
from .ssh_client import SSHClient
from .scheduler import scheduler
from .ws_manager import ws_manager
from .execution_manager import execution_manager, ExecutionCancelledError


# 节点管理
def create_node(engine: Engine, node: schemas.NodeCreate) -> dict:
    data = node.model_dump()
    stmt = insert(models.nodes_table).values(**data)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        node_id = result.inserted_primary_key[0]
        return {"id": node_id, **data}  # ✅ 返回完整对象

def get_nodes(engine: Engine, active_only: bool) -> list[dict]:
    stmt = select(models.nodes_table).order_by(models.nodes_table.c.name )
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

def delete_node(engine: Engine, node_id: int) -> bool:
    stmt = delete(models.nodes_table).where(models.nodes_table.c.id == node_id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount > 0
def toggle_node_status(engine: Engine, node_id: int, is_active: bool) -> bool:
    with engine.begin() as conn:
        # 1️⃣ 更新节点状态
        result = conn.execute(
            update(models.nodes_table)
            .where(models.nodes_table.c.id == node_id)
            .values(is_active=is_active)
        )
        if result.rowcount == 0:
            return False

        # 2️⃣ 查询该节点下所有任务
        jobs = conn.execute(
            select(models.cron_jobs_table)
            .where(models.cron_jobs_table.c.node_id == node_id)
        ).mappings().all()

    # 3️⃣ 同步调度器（事务外）
    for job in jobs:
        if is_active:
            # 节点恢复：只恢复原本启用的任务
            if job["is_active"]:
                scheduler.add_job(job)
        else:
            # 节点停用：全部从调度器移除
            scheduler.remove_job(job["id"], job["name"])

    return True

def batch_delete_nodes(engine: Engine, node_ids: list[int]) -> int:
    """批量删除节点，返回成功删除的数量"""
    deleted_count = 0

    with engine.begin() as conn:
        for node_id in node_ids:
            try:
                # 1. 删除关联的定时任务
                conn.execute(
                    delete(models.cron_jobs_table)
                    .where(models.cron_jobs_table.c.node_id == node_id)
                )

                # 2. 删除节点
                result = conn.execute(
                    delete(models.nodes_table)
                    .where(models.nodes_table.c.id == node_id)
                )

                if result.rowcount > 0:
                    deleted_count += 1

            except Exception as e:
                print(f"删除节点 {node_id} 失败: {e}")
                # 继续处理其他节点

    return deleted_count

# 任务管理
def create_cron_job(engine: Engine, job: schemas.CronJobCreate) -> dict:
    data = job.model_dump()
    stmt = insert(models.cron_jobs_table).values(**data)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        job_id = result.inserted_primary_key[0]
        return {"id": job_id, **data}  # ✅ 返回完整对象

def get_cron_jobs(engine: Engine, node_ids: list[int] = None) -> list[dict]:
    stmt = (
        select(models.cron_jobs_table)
        .join(
            models.nodes_table,
            models.cron_jobs_table.c.node_id == models.nodes_table.c.id
        )
        .where(models.nodes_table.c.is_active.is_(True))
        .order_by(models.cron_jobs_table.c.name, models.nodes_table.c.name)
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

# 执行任务
def execute_job(engine: Engine, job_id: int, triggered_by: str = "manual") -> dict:
    # 获取任务和节点（提前验证）
    with engine.connect() as conn:
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            raise ValueError(f"任务 {job_id} 不存在")

        node_stmt = select(models.nodes_table).where(models.nodes_table.c.id == job['node_id'])
        node = conn.execute(node_stmt).mappings().first()
        if not node:
            raise ValueError(f"任务 {job_id} 的节点不存在")

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

    # 异步执行
    # def run_task():
    #     try:
    #         ssh = SSHClient(schemas.NodeRead(**node))
    #         ssh.connect()
    #
    #         initial_log = {
    #             "status": "running",
    #             "output": "正在连接...\n",
    #             "error": "",
    #             "end_time": None
    #         }
    #         ws_manager.send_log_sync(execution_id, initial_log)
    #
    #         _, stdout, stderr = ssh.client.exec_command(job['command'], timeout=60)
    #         output_buffer = []
    #         error_buffer = []
    #
    #         while True:
    #             if stdout.channel.recv_ready():
    #                 line = stdout.channel.recv(1024).decode('utf-8', errors='replace')
    #                 if line:
    #                     output_buffer.append(line)
    #                     log_data = {
    #                         "status": "running",
    #                         "output": "".join(output_buffer),
    #                         "error": "".join(error_buffer),
    #                         "end_time": None
    #                     }
    #                     ws_manager.send_log_sync(execution_id, log_data)
    #
    #             if stderr.channel.recv_stderr_ready():
    #                 line = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
    #                 if line:
    #                     error_buffer.append(line)
    #                     log_data = {
    #                         "status": "running",
    #                         "output": "".join(output_buffer),
    #                         "error": "".join(error_buffer),
    #                         "end_time": None
    #                     }
    #                     ws_manager.send_log_sync(execution_id, log_data)
    #
    #             if stdout.channel.exit_status_ready():
    #                 break
    #
    #         exit_code = stdout.channel.recv_exit_status()
    #         status = "success" if exit_code == 0 else "failed"
    #         final_log = {
    #             "status": status,
    #             "output": "".join(output_buffer),
    #             "error": "".join(error_buffer),
    #             "end_time": datetime.now().isoformat()
    #         }
    #         ws_manager.send_log_sync(execution_id, final_log)
    #         _update_execution_log(engine, execution_id, "".join(output_buffer), "".join(error_buffer), status)
    #
    #     except Exception as e:
    #         error_msg = str(e)
    #         final_log = {
    #             "status": "failed",
    #             "output": "",
    #             "error": error_msg,
    #             "end_time": datetime.now().isoformat()
    #         }
    #         ws_manager.send_log_sync(execution_id, final_log)
    #         _update_execution_log(engine, execution_id, "", error_msg, "failed")
    #     finally:
    #         ssh.close()
    def run_task():
        ssh = None
        try:
            # 创建停止事件
            execution_manager.create_execution(execution_id)

            ssh = SSHClient(schemas.NodeRead(**node))
            ssh.connect()

            initial_log = {"status": "running", "output": "正在连接...\n", "error": "", "end_time": None}
            ws_manager.send_log_sync(execution_id, initial_log)

            _, stdout, stderr = ssh.client.exec_command(job['command'], timeout=60)
            output_buffer = []
            error_buffer = []

            while True:
                # 检查是否需要中断
                if execution_manager.should_stop(execution_id):
                    raise ExecutionCancelledError("任务已被用户中断")
                if stdout.channel.recv_ready():
                    line = stdout.channel.recv(1024).decode('utf-8', errors='replace')
                    if line:
                        output_buffer.append(line)
                        log_data = {
                            "status": "running",
                            "output": "".join(output_buffer),
                            "error": "".join(error_buffer),
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)
                if stderr.channel.recv_stderr_ready():
                    line = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
                    if line:
                        error_buffer.append(line)
                        log_data = {
                            "status": "running",
                            "output": "".join(output_buffer),
                            "error": "".join(error_buffer),
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)

                if stdout.channel.exit_status_ready():
                    # stdout 兜底
                    while stdout.channel.recv_ready():
                        output_buffer.append(
                            stdout.channel.recv(4096).decode("utf-8", errors="replace")
                        )

                    # stderr 兜底
                    while stderr.channel.recv_stderr_ready():
                        error_buffer.append(
                            stderr.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                        )
                    break

            exit_code = stdout.channel.recv_exit_status()
            status = "success" if exit_code == 0 else "failed"
            final_log = {
                "status": status,
                "output": "".join(output_buffer),
                "error": "".join(error_buffer),
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)
            _update_execution_log(engine, execution_id, "".join(output_buffer), "".join(error_buffer), status)
        except ExecutionCancelledError as e:
            # 👇 用户中断：状态 = cancelled
            error_msg = str(e)
            final_log = {
                "status": "cancelled",
                "output": "".join(output_buffer) if 'output_buffer' in locals() else "",
                "error": error_msg,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)
            _update_execution_log(engine, execution_id, final_log["output"], error_msg, "cancelled")
        except Exception as e:
            error_msg = str(e)
            final_log = {
                "status": "failed",
                "output": "",
                "error": error_msg,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)
            _update_execution_log(engine, execution_id, "", error_msg, "failed")
        finally:
            if ssh:
                ssh.close()
            # 清理资源
            execution_manager.cleanup(execution_id)
    threading.Thread(target=run_task, daemon=True).start()

    # ✅ 返回初始执行记录
    return get_execution(engine, execution_id)

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

# ✅ 修正参数顺序：engine 放第一位
def _update_execution_log(engine: Engine, execution_id: int, output: str, error: str, status: str):
    max_length = 5000
    truncated_output = output[-max_length:] if len(output) > max_length else output
    truncated_error = error[-max_length:] if len(error) > max_length else error

    stmt = (
        update(models.job_executions_table)
        .where(models.job_executions_table.c.id == execution_id)
        .values(
            output=truncated_output,
            error=truncated_error,
            status=status,
            end_time=datetime.now() if status in ["success", "failed"] else None
        )
    )
    with engine.begin() as conn:
        conn.execute(stmt)

