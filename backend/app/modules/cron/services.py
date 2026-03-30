from croniter import croniter
from sqlalchemy import select, insert, update, delete, desc, Engine
from datetime import datetime
import threading
import logging
from typing import List, Optional

from app.core.sh.ssh_client import SSHClient
from app.core.ws.ws_manager import ws_manager
from app.core.interrupt.execution_manager import execution_manager, ExecutionCancelledError
from app.core.scheduler import scheduler_service  # 导入新的调度器服务

from app.modules.node.models import nodes_table
from . import models, schemas

logger = logging.getLogger(__name__)


# ========== 任务管理基础函数 ==========

def create_cron_job(engine: Engine, job: schemas.CronJobCreate) -> dict:
    """创建定时任务"""
    data = job.model_dump()
    stmt = insert(models.cron_jobs_table).values(**data)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        job_id = result.inserted_primary_key[0]

        # 创建成功后，如果是启用状态，添加到调度器
        if job.is_active:
            _add_job_to_scheduler(engine, job_id)

        return {"id": job_id, **data}


def get_cron_jobs(engine: Engine, node_ids: list[int] = None) -> list[dict]:
    """获取所有定时任务"""
    stmt = (
        select(models.cron_jobs_table)
        .join(
            nodes_table,
            models.cron_jobs_table.c.node_id == nodes_table.c.id
        )
        .where(nodes_table.c.is_active.is_(True))
        .order_by(models.cron_jobs_table.c.name, nodes_table.c.name)
    )

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


def get_cron_job(engine: Engine, job_id: int) -> Optional[dict]:
    """获取单个定时任务"""
    with engine.connect() as conn:
        query = models.cron_jobs_table.select().where(models.cron_jobs_table.c.id == job_id)
        result = conn.execute(query).fetchone()
        return result._asdict() if result else None


def update_cron_job(engine: Engine, job_id: int, update_data: dict) -> bool:
    """更新定时任务"""
    with engine.connect() as conn:
        # 获取旧的任务信息
        old_job = get_cron_job(engine, job_id)
        if not old_job:
            return False

        stmt = (
            update(models.cron_jobs_table)
            .where(models.cron_jobs_table.c.id == job_id)
            .values(**update_data)
        )
        result = conn.execute(stmt)
        conn.commit()

        if result.rowcount > 0:
            # 处理调度器中的任务
            full_job_id = f"cron_jobs:{job_id}"

            # 如果状态或调度表达式变化，需要重新加载
            is_active_changed = 'is_active' in update_data and update_data['is_active'] != old_job['is_active']
            schedule_changed = 'schedule' in update_data and update_data['schedule'] != old_job['schedule']

            if is_active_changed or schedule_changed:
                # 先移除旧任务
                if full_job_id in scheduler_service.job_ids:
                    scheduler_service.remove_job(full_job_id)

                # 如果新状态是启用，添加新任务
                new_is_active = update_data.get('is_active', old_job['is_active'])
                if new_is_active:
                    _add_job_to_scheduler(engine, job_id)

            return True
        return False


def toggle_job_status(engine: Engine, job_id: int, is_active: bool) -> bool:
    """切换任务状态"""
    stmt = (
        update(models.cron_jobs_table)
        .where(models.cron_jobs_table.c.id == job_id)
        .values(is_active=is_active)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            return False

        full_job_id = f"cron_jobs:{job_id}"

        if is_active:
            # 启用任务
            _add_job_to_scheduler(engine, job_id)
        else:
            # 禁用任务
            if full_job_id in scheduler_service.job_ids:
                scheduler_service.remove_job(full_job_id)

        return True


def remove_job(engine: Engine, job_id: int) -> bool:
    """删除定时任务"""
    with engine.begin() as conn:
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            return False

        stmt = delete(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        result = conn.execute(stmt)

        # 从调度器移除
        full_job_id = f"cron_jobs:{job_id}"
        if full_job_id in scheduler_service.job_ids:
            scheduler_service.remove_job(full_job_id)

        return result.rowcount > 0


def _add_job_to_scheduler(engine: Engine, job_id: int) -> bool:
    """将任务添加到调度器（内部函数）"""
    from app.core.scheduler.base import JobInfo

    job = get_cron_job(engine, job_id)

    # 检查节点是否活跃
    with engine.connect() as conn:
        node_stmt = select(nodes_table.c.is_active).where(nodes_table.c.id == job['node_id'])
        node_active = conn.execute(node_stmt).scalar()
        if not node_active:
            logger.warning(f"任务 {job_id} 的节点不活跃，跳过添加到调度器")
            return False

    job_info = JobInfo(
        job_id=str(job_id),
        name=job['name'],
        schedule=job['schedule'],
        module="cron_jobs",
        enabled=True,
        params={'node_id': job['node_id']},
        description=job.get('description', '')
    )

    return scheduler_service.add_job(job_info)


# ========== 任务执行相关函数 ==========

def execute_job(engine: Engine, job_id: int, triggered_by: str = "manual", inputs: dict = None, outputs: dict = None) -> dict:
    """执行任务并实时保存日志"""
    # 获取任务和节点（提前验证）
    with engine.connect() as conn:
        job_stmt = select(models.cron_jobs_table).where(models.cron_jobs_table.c.id == job_id)
        job = conn.execute(job_stmt).mappings().first()
        if not job:
            # 从调度器移除
            full_job_id = f"cron_jobs:{job_id}"
            if full_job_id in scheduler_service.job_ids:
                scheduler_service.remove_job(full_job_id)
            raise ValueError(f"任务 {job_id} 不存在，已移除计划")

        node_stmt = select(nodes_table).where(nodes_table.c.id == job['node_id'])
        node = conn.execute(node_stmt).mappings().first()
        if not node:
            full_job_id = f"cron_jobs:{job_id}"
            if full_job_id in scheduler_service.job_ids:
                scheduler_service.remove_job(full_job_id)
            raise ValueError(f"任务 {job_id} 的节点{job['node_id']}不存在，已移除计划")

    # 替换命令中的输入参数和输出参数
    command = job['command']
    logger.debug(f"原始命令: {command}")
    logger.debug(f"输入参数: {inputs}")
    logger.debug(f"输出参数: {outputs}")

    # 替换输入参数 {{inputs.xxx}}
    if inputs:
        for key, value in inputs.items():
            placeholder = f"{{inputs.{key}}}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))
                logger.debug(f"替换输入参数: {placeholder} -> {value}")

    # 替换输出参数 {{outputs.node_id}} 或 {{outputs.node_id.xxx}}
    if outputs:
        import re
        output_pattern = r'\{\{outputs\.(\w+)(?:\.(\w+))?\}\}'
        matches = re.findall(output_pattern, command)

        for node_id, field in matches:
            if node_id in outputs:
                node_output = outputs[node_id]
                if field:
                    # 替换特定字段 {{outputs.node_id.output}}
                    value = node_output.get(field, "")
                    placeholder = f"{{outputs.{node_id}.{field}}}"
                else:
                    # 替换整个输出对象 {{outputs.node_id}}
                    value = str(node_output)
                    placeholder = f"{{outputs.{node_id}}}"

                if placeholder in command:
                    command = command.replace(placeholder, str(value))
                    logger.info(f"替换输出参数: {placeholder} -> {value}")

    logger.debug(f"最终命令: {command}")

    # 工作流调用时，同步执行任务；否则后台执行
    if triggered_by == "workflow":
        # 同步执行模式：直接执行并等待完成
        return _execute_job_sync(engine, job_id, command, node, job, inputs, outputs)
    else:
        # 后台执行模式：在后台线程中执行
        return _execute_job_async(engine, job_id, command, node, job, triggered_by)


def _execute_job_sync(engine: Engine, job_id: int, command: str, node: dict, job: dict, inputs: dict = None, outputs: dict = None) -> dict:
    """同步执行任务（用于工作流）"""
    ssh = None
    output_buffer = []
    error_buffer = []

    # 创建执行记录
    stmt = insert(models.job_executions_table).values(
        job_id=job_id,
        start_time=datetime.now(),
        status="running",
        triggered_by="workflow"
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        execution_id = result.inserted_primary_key[0]
        logger.info(f"✅ 工作流任务调度：时间（{datetime.now().replace(second=0, microsecond=0)}），设备（{node['name']}），任务（{job['name']}）")

    try:
        # 初始化执行日志
        _init_execution_log(engine, execution_id)

        from app.modules.node.schemas import NodeRead
        ssh = SSHClient(NodeRead(**node))
        ssh.connect()

        _, stdout, stderr = ssh.client.exec_command(command, timeout=60)

        while True:
            if stdout.channel.recv_ready():
                line = stdout.channel.recv(1024).decode('utf-8', errors='replace')
                if line:
                    output_buffer.append(line)

            if stderr.channel.recv_stderr_ready():
                line = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
                if line:
                    error_buffer.append(line)

            if stdout.channel.exit_status_ready():
                while stdout.channel.recv_ready():
                    line = stdout.channel.recv(4096).decode("utf-8", errors="replace")
                    if line:
                        output_buffer.append(line)

                while stderr.channel.recv_stderr_ready():
                    line = stderr.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    if line:
                        error_buffer.append(line)

                break

        exit_code = stdout.channel.recv_exit_status()
        status = "success" if exit_code == 0 else "failed"

        final_output = "".join(output_buffer)
        final_error = "".join(error_buffer)

        # 保存输出和错误日志
        if output_buffer or error_buffer:
            _save_and_clear_buffer(engine, execution_id, output_buffer, error_buffer, status)

        # 更新最终状态
        _update_execution_final_status(engine, execution_id, status, job, final_error)

        logger.info(f"任务执行完成: job_id={job_id}, status={status}, output={final_output[:100] if final_output else ''}, error={final_error[:100] if final_error else ''}")

        return {
            "status": status,
            "output": final_output,
            "error": final_error
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"任务执行异常: job_id={job_id}, error={error_msg}")

        # 保存错误日志
        if error_buffer:
            _save_and_clear_buffer(engine, execution_id, [], error_buffer, "failed")

        # 更新最终状态
        _update_execution_final_status(engine, execution_id, "failed", job, error_msg)

        return {
            "status": "failed",
            "output": "",
            "error": error_msg
        }

    finally:
        if ssh:
            ssh.close()


def _execute_job_async(engine: Engine, job_id: int, command: str, node: dict, job: dict, triggered_by: str) -> dict:
    """异步执行任务（用于手动执行和调度）"""

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
        logger.info(f"✅ 任务调度：时间（{datetime.now().replace(second=0, microsecond=0)}），设备（{node['name']}），任务（{job['name']}），触发方式（{triggered_by}）")

    def run_task():
        ssh = None
        output_buffer = []
        error_buffer = []
        out_len = 2000
        error_len = 1000

        try:
            execution_manager.create_execution(execution_id)
            _init_execution_log(engine, execution_id)

            from app.modules.node.schemas import NodeRead
            ssh = SSHClient(NodeRead(**node))
            ssh.connect()

            initial_log = {"status": "running", "output": "正在连接...\n", "error": "", "end_time": None}
            ws_manager.send_log_sync(execution_id, initial_log)

            _, stdout, stderr = ssh.client.exec_command(command, timeout=60)

            while True:
                if execution_manager.should_stop(execution_id):
                    raise ExecutionCancelledError("任务已被用户中断")

                if stdout.channel.recv_ready():
                    line = stdout.channel.recv(1024).decode('utf-8', errors='replace')
                    if line:
                        output_buffer.append(line)
                        log_data = {
                            "status": "running",
                            "output": line,
                            "error": "",
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)

                        if len("".join(output_buffer)) >= out_len:
                            _save_and_clear_buffer(engine, execution_id, output_buffer, [], "running")

                if stderr.channel.recv_stderr_ready():
                    line = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
                    if line:
                        error_buffer.append(line)
                        log_data = {
                            "status": "running",
                            "output": "",
                            "error": line,
                            "end_time": None
                        }
                        ws_manager.send_log_sync(execution_id, log_data)

                        if len("".join(error_buffer)) >= error_len:
                            _save_and_clear_buffer(engine, execution_id, [], error_buffer, "running")

                if stdout.channel.exit_status_ready():
                    while stdout.channel.recv_ready():
                        line = stdout.channel.recv(4096).decode("utf-8", errors="replace")
                        if line:
                            output_buffer.append(line)
                            log_data = {"status": "running", "output": line, "error": "", "end_time": None}
                            ws_manager.send_log_sync(execution_id, log_data)

                    while stderr.channel.recv_stderr_ready():
                        line = stderr.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                        if line:
                            error_buffer.append(line)
                            log_data = {"status": "running", "output": "", "error": line, "end_time": None}
                            ws_manager.send_log_sync(execution_id, log_data)

                    break

            if output_buffer:
                _save_and_clear_buffer(engine, execution_id, output_buffer, [], "running")
            if error_buffer:
                _save_and_clear_buffer(engine, execution_id, [], error_buffer, "running")

            exit_code = stdout.channel.recv_exit_status()
            status = "success" if exit_code == 0 else "failed"

            final_output = "".join(output_buffer)
            final_error = "".join(error_buffer)

            _update_execution_final_status(engine, execution_id, status, job, final_error)

            final_log = {
                "status": status,
                "output": final_output,
                "error": final_error,
                "end_time": datetime.now().isoformat()
            }
            ws_manager.send_log_sync(execution_id, final_log)

        except ExecutionCancelledError as e:
            error_msg = str(e)
            if output_buffer:
                _save_and_clear_buffer(engine, execution_id, output_buffer, [], "cancelled")
            if error_msg:
                _save_and_clear_buffer(engine, execution_id, [], [error_msg], "cancelled")

            _update_execution_final_status(engine, execution_id, "cancelled", job, error_msg)

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
            _save_and_clear_buffer(engine, execution_id, [], [error_msg], "failed")
            _update_execution_final_status(engine, execution_id, "failed", job, error_msg)

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
            execution_manager.cleanup(execution_id)
            ws_manager.cleanup(execution_id)

    threading.Thread(target=run_task, daemon=True).start()
    return get_execution(engine, execution_id)


def execute_jobs(engine: Engine, request: schemas.ManualExecutionRequest) -> list[dict]:
    """批量执行任务"""
    results = []
    for job_id in request.job_ids:
        execution = execute_job(engine, job_id, "manual")
        results.append(execution)
    return results


# ========== 执行记录相关函数 ==========

def get_executions(engine: Engine, job_id: int, limit: int = 10) -> list[dict]:
    """获取执行记录"""
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
    """获取单个执行记录"""
    stmt = select(models.job_executions_table).where(models.job_executions_table.c.id == execution_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        return dict(result) if result else None


# ========== 内部辅助函数 ==========

def _init_execution_log(engine: Engine, execution_id: int):
    """初始化执行日志记录"""
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

    output_buffer.clear()
    error_buffer.clear()


def _update_execution_final_status(engine: Engine, execution_id: int, status: str, job: dict, error: str = ''):
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

        from app.modules.cron.schemas import CronJobUpdateNotice
        job = CronJobUpdateNotice(**job)

        if status == 'success':
            stmt1 = (
                update(models.cron_jobs_table)
                .where(models.cron_jobs_table.c.id == job.id)
                .values(consecutive_failures=0)
            )
        elif status == 'failed':
            new_failures = (0 if not job.consecutive_failures else job.consecutive_failures) + 1

            if new_failures >= job.error_times:
                from app.modules.notify.handler.manager import notification_manager
                import asyncio
                asyncio.run(notification_manager.send_broadcast(
                    content=f"任务【{job.name}】连续失败 {new_failures} 次。\n"
                            f"次数清零！\n"
                            f"{'' if error == '详情：无！' else f'详情：{error}'}"
                ))
                stmt1 = (
                    update(models.cron_jobs_table)
                    .where(models.cron_jobs_table.c.id == job.id)
                    .values(consecutive_failures=0)
                )
            else:
                stmt1 = (
                    update(models.cron_jobs_table)
                    .where(models.cron_jobs_table.c.id == job.id)
                    .values(consecutive_failures=new_failures)
                )
        conn.execute(stmt1)


def get_next_crons(cron: schemas.CronReq) -> list[dict]:
    """获取未来的执行时间"""
    cron = croniter(cron.cron, datetime.now())
    recent_runs = []
    for _ in range(5):
        next_run = cron.get_next(datetime)
        recent_runs.append(schemas.CronNextRes(next_run=next_run.isoformat()))
    return recent_runs


# ========== 调度器同步函数 ==========

def sync_all_jobs_to_scheduler(engine: Engine) -> int:
    """将所有启用的任务同步到调度器"""
    from .job_provider import cron_job_provider

    count = 0
    jobs = get_cron_jobs(engine)

    for job in jobs:
        if job['is_active']:
            full_job_id = f"cron_jobs:{job['id']}"
            if full_job_id not in scheduler_service.job_ids:
                if _add_job_to_scheduler(engine, job['id']):
                    count += 1

    logger.info(f"同步了 {count} 个任务到调度器")
    return count


def reload_all_jobs(engine: Engine) -> int:
    """重新加载所有任务（先清空再添加）"""
    # 移除当前模块的所有任务
    to_remove = []
    for job_id in scheduler_service.job_ids:
        if job_id.startswith("cron_jobs:"):
            to_remove.append(job_id)

    for job_id in to_remove:
        scheduler_service.remove_job(job_id)

    # 重新添加
    return sync_all_jobs_to_scheduler(engine)
