# app/modules/workflow/job_provider.py
"""
工作流模块 - 定时任务提供者

参考 cron 模块的 job_provider.py 实现
"""
from typing import List
import logging
from app.core.scheduler.base import JobProvider, JobInfo
from app.core.db.database import engine
from . import services, models

logger = logging.getLogger(__name__)


class WorkflowJobProvider(JobProvider):
    """工作流定时任务提供者"""
    
    def get_module_name(self) -> str:
        return "workflows"

    def get_enabled_jobs(self) -> List[JobInfo]:
        """获取所有启用的工作流（有 schedule 的）"""
        jobs = []
        db_workflows = services.WorkflowService(engine).get_all()
        
        for workflow in db_workflows:
            if workflow['is_active'] and workflow.get('schedule'):
                jobs.append(JobInfo(
                    job_id=str(workflow['id']),
                    name=workflow['name'],
                    schedule=workflow['schedule'],
                    module=self.get_module_name(),
                    enabled=True,
                    params={'workflow_id': workflow['workflow_id']},
                    description=workflow.get('description', '')
                ))
        return jobs

    def execute_job(self, job_info: JobInfo) -> any:
        """执行工作流"""
        workflow_id = job_info.params.get('workflow_id')
        if not workflow_id:
            logger.error(f"工作流ID为空: {job_info.name}")
            return None
        
        try:
            from app.modules.workflow.engine import WorkflowEngine
            workflow_engine = WorkflowEngine(engine)
            
            # 创建执行记录
            execution_id = workflow_engine.create_execution(
                workflow_id=workflow_id,
                triggered_by="schedule",
                inputs={}
            )
            
            # 执行工作流
            import asyncio
            asyncio.run(workflow_engine.execute(execution_id))
            
            logger.info(f"工作流执行完成: {workflow_id}, execution_id={execution_id}")
            return execution_id
        except Exception as e:
            logger.error(f"工作流执行失败: {workflow_id}, error: {e}")
            return None

    def on_job_added(self, job_info: JobInfo) -> None:
        """工作流添加到调度器时的回调"""
        logger.info(f"🆕 工作流已添加到调度器: {job_info.name}")

    def on_job_removed(self, job_info: JobInfo) -> None:
        """工作流从调度器移除时的回调"""
        logger.info(f"🗑️ 工作流已从调度器移除: {job_info.name}")

    def on_job_executed(self, job_info: JobInfo, result: any, error: Exception) -> None:
        """工作流执行后的回调"""
        if error:
            logger.error(f"❌ 工作流执行失败: {job_info.name} - {error}")
        else:
            logger.info(f"✅ 工作流执行成功: {job_info.name}")


workflow_job_provider = WorkflowJobProvider()
