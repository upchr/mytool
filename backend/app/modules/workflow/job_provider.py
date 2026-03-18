from typing import List
import logging
from app.core.scheduler.base import JobProvider, JobInfo
from app.core.db.database import database
from . import services
from .engine import workflow_engine

logger = logging.getLogger(__name__)


class WorkflowJobProvider(JobProvider):
    def get_module_name(self) -> str:
        return "workflows"

    def get_enabled_jobs(self) -> List[JobInfo]:
        jobs = []
        
        # 获取所有启用且有 schedule 的工作流
        from sqlalchemy import select
        from .models import workflows_table
        
        query = select(workflows_table).where(
            workflows_table.c.is_active == True,
            workflows_table.c.schedule.is_not(None)
        )
        
        with database.engine.connect() as conn:
            result = conn.execute(query)
            for row in result.mappings():
                if row["schedule"]:
                    jobs.append(JobInfo(
                        job_id=row["workflow_id"],
                        name=row["name"],
                        schedule=row["schedule"],
                        module=self.get_module_name(),
                        enabled=True,
                        params={"workflow_id": row["workflow_id"]},
                        description=row.get("description", "")
                    ))
        
        return jobs

    def execute_job(self, job_info: JobInfo) -> any:
        import asyncio
        
        workflow_id = job_info.params.get("workflow_id")
        if not workflow_id:
            raise ValueError("workflow_id 参数缺失")
        
        logger.info(f"定时触发工作流: {workflow_id}")
        
        # 在同步函数中运行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            execution_id = loop.run_until_complete(
                workflow_engine.start_workflow(
                    workflow_id,
                    triggered_by="schedule"
                )
            )
            return {"execution_id": execution_id, "workflow_id": workflow_id}
        finally:
            loop.close()

    def on_job_added(self, job_info: JobInfo) -> None:
        logger.info(f"🆕 工作流已添加到调度器: {job_info.name}")

    def on_job_removed(self, job_info: JobInfo) -> None:
        logger.info(f"🗑️ 工作流已从调度器移除: {job_info.name}")

    def on_job_executed(self, job_info: JobInfo, result: any, error: Exception) -> None:
        if error:
            logger.error(f"❌ 工作流执行失败: {job_info.name} - {error}")
        else:
            logger.info(f"✅ 工作流执行成功: {job_info.name}, result={result}")


workflow_job_provider = WorkflowJobProvider()