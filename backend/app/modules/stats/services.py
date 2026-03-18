from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from app.core.db.database import database, engine
from app.modules.cron.models import cron_jobs_table, job_executions_table
from app.modules.workflow.models import workflows_table, workflow_executions_table
import logging

logger = logging.getLogger(__name__)


class StatsService:
    """统计服务"""

    @staticmethod
    async def get_overview() -> Dict[str, Any]:
        """获取系统概览统计"""
        # Cron 任务统计
        cron_total_query = select(func.count()).where(cron_jobs_table.c.is_active == True)
        cron_total = await database.fetch_val(cron_total_query) or 0
        
        cron_active_query = select(func.count()).where(
            and_(cron_jobs_table.c.is_active == True, cron_jobs_table.c.is_active == True)
        )
        cron_active = await database.fetch_val(cron_active_query) or 0
        
        # 最近24小时 cron 执行统计
        yesterday = datetime.utcnow() - timedelta(days=1)
        cron_exec_24h_query = select(func.count()).where(
            job_executions_table.c.start_time >= yesterday
        )
        cron_exec_24h = await database.fetch_val(cron_exec_24h_query) or 0
        
        cron_success_24h_query = select(func.count()).where(
            and_(
                job_executions_table.c.start_time >= yesterday,
                job_executions_table.c.status == "success"
            )
        )
        cron_success_24h = await database.fetch_val(cron_success_24h_query) or 0
        
        # Workflow 统计
        workflow_total_query = select(func.count()).where(workflows_table.c.is_active == True)
        workflow_total = await database.fetch_val(workflow_total_query) or 0
        
        workflow_active_query = select(func.count()).where(
            and_(workflows_table.c.is_active == True, workflows_table.c.is_active == True)
        )
        workflow_active = await database.fetch_val(workflow_active_query) or 0
        
        workflow_exec_24h_query = select(func.count()).where(
            workflow_executions_table.c.start_time >= yesterday
        )
        workflow_exec_24h = await database.fetch_val(workflow_exec_24h_query) or 0
        
        workflow_success_24h_query = select(func.count()).where(
            and_(
                workflow_executions_table.c.start_time >= yesterday,
                workflow_executions_table.c.status == "success"
            )
        )
        workflow_success_24h = await database.fetch_val(workflow_success_24h_query) or 0
        
        # 计算成功率
        cron_success_rate = (cron_success_24h / cron_exec_24h * 100) if cron_exec_24h > 0 else 0
        workflow_success_rate = (workflow_success_24h / workflow_exec_24h * 100) if workflow_exec_24h > 0 else 0
        
        return {
            "cron": {
                "total": cron_total,
                "active": cron_active,
                "executions_24h": cron_exec_24h,
                "success_24h": cron_success_24h,
                "success_rate_24h": round(cron_success_rate, 2)
            },
            "workflow": {
                "total": workflow_total,
                "active": workflow_active,
                "executions_24h": workflow_exec_24h,
                "success_24h": workflow_success_24h,
                "success_rate_24h": round(workflow_success_rate, 2)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def get_recent_executions(limit: int = 20) -> Dict[str, Any]:
        """获取最近的执行记录"""
        # 最近的 cron 执行
        cron_query = (
            select(job_executions_table)
            .order_by(job_executions_table.c.start_time.desc())
            .limit(limit)
        )
        cron_execs = await database.fetch_all(cron_query)
        
        # 最近的 workflow 执行
        workflow_query = (
            select(workflow_executions_table)
            .order_by(workflow_executions_table.c.start_time.desc())
            .limit(limit)
        )
        workflow_execs = await database.fetch_all(workflow_query)
        
        # 合并并排序
        all_execs = []
        for exec in cron_execs:
            all_execs.append({
                "type": "cron",
                "id": exec["id"],
                "name": f"Cron Job {exec['job_id']}",
                "status": exec["status"],
                "start_time": exec["start_time"].isoformat() if exec["start_time"] else None,
                "end_time": exec["end_time"].isoformat() if exec["end_time"] else None
            })
        
        for exec in workflow_execs:
            all_execs.append({
                "type": "workflow",
                "id": exec["id"],
                "name": f"Workflow {exec['workflow_id']}",
                "status": exec["status"],
                "start_time": exec["start_time"].isoformat() if exec["start_time"] else None,
                "end_time": exec["end_time"].isoformat() if exec["end_time"] else None
            })
        
        # 按时间排序
        all_execs.sort(key=lambda x: x["start_time"] or "", reverse=True)
        
        return {
            "executions": all_execs[:limit],
            "total": len(all_execs)
        }