# app/modules/acme/job_provider.py
from typing import List
import logging
from app.core.scheduler.base import JobProvider, JobInfo

logger = logging.getLogger(__name__)


class SslJobProvider(JobProvider):
    def get_module_name(self) -> str:
        return "ssl_jobs"

    def get_all_jobs(self) -> List[JobInfo]:
        jobs = []
        # db_jobs = services.get_ssl_jobs(engine)
        db_jobs = []

        for job in db_jobs:
            jobs.append(JobInfo(
                job_id=str(job['id']),
                name=job['name'],
                schedule=job['schedule'],
                module=self.get_module_name(),
                enabled=job['is_active'],
                params={'node_id': job['node_id']},
                description=job.get('description', '')
            ))
        return jobs

    def get_enabled_jobs(self) -> List[JobInfo]:
        jobs = []
        db_jobs = []
        # db_jobs = services.get_ssl_jobs(engine)

        for job in db_jobs:
            if job['is_active']:
                jobs.append(JobInfo(
                    job_id=str(job['id']),
                    name=job['name'],
                    schedule=job['schedule'],
                    module=self.get_module_name(),
                    enabled=True,
                    params={'node_id': job['node_id']},
                    description=job.get('description', '')
                ))
        return jobs

    def execute_job(self, job_info: JobInfo) -> any:
        job_id = int(job_info.job_id)
        return False
        # return services.execute_job(engine, job_id, triggered_by="system")

    def on_job_added(self, job_info: JobInfo) -> None:
        logger.info(f"🆕 任务已添加到调度器: {job_info.name}")

    def on_job_removed(self, job_info: JobInfo) -> None:
        logger.info(f"🗑️ 任务已从调度器移除: {job_info.name}")

    def on_job_executed(self, job_info: JobInfo, result: any, error: Exception) -> None:
        if error:
            logger.error(f"❌ 任务执行失败: {job_info.name} - {error}")
        else:
            logger.info(f"✅ 任务执行成功: {job_info.name}")


ssl_job_provider = SslJobProvider()
