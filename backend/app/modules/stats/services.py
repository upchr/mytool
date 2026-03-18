# app/modules/stats/services.py
"""
统计模块 - 业务逻辑层

提供系统运行统计和概览数据
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


class StatsService:
    """系统统计服务"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_overview(self) -> Dict[str, Any]:
        """
        获取系统概览统计
        
        Returns:
            包含 cron、workflow 等统计数据的字典
        """
        overview = {
            "cron": self._get_cron_stats(),
            "workflow": self._get_workflow_stats(),
            "node": self._get_node_stats(),
            "generated_at": datetime.utcnow().isoformat()
        }
        return overview
    
    def _get_cron_stats(self) -> Dict[str, Any]:
        """获取 Cron 任务统计"""
        try:
            from app.modules.cron.models import cron_jobs_table, job_executions_table
            
            # 总任务数
            total_query = select(func.count()).select_from(cron_jobs_table)
            with self.engine.connect() as conn:
                total = conn.execute(total_query).scalar() or 0
            
            # 活跃任务数
            active_query = select(func.count()).select_from(cron_jobs_table).where(
                cron_jobs_table.c.is_active == True
            )
            with self.engine.connect() as conn:
                active = conn.execute(active_query).scalar() or 0
            
            # 最近24小时执行统计
            yesterday = datetime.utcnow() - timedelta(days=1)
            exec_24h_query = select(func.count()).select_from(job_executions_table).where(
                job_executions_table.c.start_time >= yesterday
            )
            with self.engine.connect() as conn:
                exec_24h = conn.execute(exec_24h_query).scalar() or 0
            
            success_24h_query = select(func.count()).select_from(job_executions_table).where(
                and_(
                    job_executions_table.c.start_time >= yesterday,
                    job_executions_table.c.status == "success"
                )
            )
            with self.engine.connect() as conn:
                success_24h = conn.execute(success_24h_query).scalar() or 0
            
            success_rate = (success_24h / exec_24h * 100) if exec_24h > 0 else 0
            
            return {
                "total": total,
                "active": active,
                "executions_24h": exec_24h,
                "success_24h": success_24h,
                "success_rate_24h": round(success_rate, 2)
            }
        except Exception as e:
            logger.error(f"获取 Cron 统计失败: {e}")
            return {"total": 0, "active": 0, "executions_24h": 0, "success_24h": 0, "success_rate_24h": 0}
    
    def _get_workflow_stats(self) -> Dict[str, Any]:
        """获取工作流统计"""
        try:
            from app.modules.workflow.models import workflows_table, workflow_executions_table
            
            # 总工作流数
            total_query = select(func.count()).select_from(workflows_table).where(
                workflows_table.c.is_active == True
            )
            with self.engine.connect() as conn:
                total = conn.execute(total_query).scalar() or 0
            
            # 活跃工作流数
            active_query = select(func.count()).select_from(workflows_table).where(
                and_(
                    workflows_table.c.is_active == True,
                    workflows_table.c.schedule.is_not(None)
                )
            )
            with self.engine.connect() as conn:
                active = conn.execute(active_query).scalar() or 0
            
            # 最近24小时执行统计
            yesterday = datetime.utcnow() - timedelta(days=1)
            exec_24h_query = select(func.count()).select_from(workflow_executions_table).where(
                workflow_executions_table.c.start_time >= yesterday
            )
            with self.engine.connect() as conn:
                exec_24h = conn.execute(exec_24h_query).scalar() or 0
            
            success_24h_query = select(func.count()).select_from(workflow_executions_table).where(
                and_(
                    workflow_executions_table.c.start_time >= yesterday,
                    workflow_executions_table.c.status == "success"
                )
            )
            with self.engine.connect() as conn:
                success_24h = conn.execute(success_24h_query).scalar() or 0
            
            success_rate = (success_24h / exec_24h * 100) if exec_24h > 0 else 0
            
            return {
                "total": total,
                "active": active,
                "executions_24h": exec_24h,
                "success_24h": success_24h,
                "success_rate_24h": round(success_rate, 2)
            }
        except Exception as e:
            logger.error(f"获取工作流统计失败: {e}")
            return {"total": 0, "active": 0, "executions_24h": 0, "success_24h": 0, "success_rate_24h": 0}
    
    def _get_node_stats(self) -> Dict[str, Any]:
        """获取节点统计"""
        try:
            from app.modules.node.models import nodes_table
            
            # 总节点数
            total_query = select(func.count()).select_from(nodes_table)
            with self.engine.connect() as conn:
                total = conn.execute(total_query).scalar() or 0
            
            # 活跃节点数（最近5分钟有心跳）
            recent = datetime.utcnow() - timedelta(minutes=5)
            active_query = select(func.count()).select_from(nodes_table).where(
                nodes_table.c.last_heartbeat >= recent
            )
            with self.engine.connect() as conn:
                active = conn.execute(active_query).scalar() or 0
            
            return {
                "total": total,
                "active": active
            }
        except Exception as e:
            logger.error(f"获取节点统计失败: {e}")
            return {"total": 0, "active": 0}
    
    def get_recent_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取最近的执行记录
        
        Args:
            limit: 返回条数
        
        Returns:
            执行记录列表
        """
        executions = []
        
        try:
            # Cron 执行记录
            from app.modules.cron.models import job_executions_table
            
            query = (
                select(job_executions_table)
                .order_by(job_executions_table.c.start_time.desc())
                .limit(limit)
            )
            with self.engine.connect() as conn:
                result = conn.execute(query)
                for row in result:
                    executions.append({
                        "type": "cron",
                        "id": row["id"],
                        "name": f"Cron Job {row['job_id']}",
                        "status": row["status"],
                        "start_time": row["start_time"].isoformat() if row["start_time"] else None,
                        "end_time": row["end_time"].isoformat() if row["end_time"] else None
                    })
        except Exception as e:
            logger.error(f"获取 Cron 执行记录失败: {e}")
        
        try:
            # Workflow 执行记录
            from app.modules.workflow.models import workflow_executions_table
            
            query = (
                select(workflow_executions_table)
                .order_by(workflow_executions_table.c.start_time.desc())
                .limit(limit)
            )
            with self.engine.connect() as conn:
                result = conn.execute(query)
                for row in result:
                    executions.append({
                        "type": "workflow",
                        "id": row["id"],
                        "name": f"Workflow {row['workflow_id']}",
                        "status": row["status"],
                        "start_time": row["start_time"].isoformat() if row["start_time"] else None,
                        "end_time": row["end_time"].isoformat() if row["end_time"] else None
                    })
        except Exception as e:
            logger.error(f"获取工作流执行记录失败: {e}")
        
        # 按时间排序并截取
        executions.sort(key=lambda x: x["start_time"] or "", reverse=True)
        return executions[:limit]


__all__ = ["StatsService"]
