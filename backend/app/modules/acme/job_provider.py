# app/modules/acme/job_provider.py
import json
from typing import List
import logging

from app.core.db.database import engine
from app.core.scheduler.base import JobProvider, JobInfo
from app.modules.acme.ssl_repository import ApplicationRepository

logger = logging.getLogger(__name__)


class SslJobProvider(JobProvider):
    def get_module_name(self) -> str:
        return "ssl_jobs"

    def get_enabled_jobs(self) -> List[JobInfo]:
        return [JobInfo(
            job_id="renewal_check",
            name="证书续期定时检查",
            schedule='0 2 * * *',  # 0 2 * * *
            # schedule='*/5 * * * *',  # 0 2 * * *
            module=self.get_module_name(),
            params={}
        )]

    def execute_job(self, job_info: JobInfo) -> any:
        pending = ApplicationRepository(engine).get_pending_renew()

        for app in pending:
            self._renew_certificate(app)

    def _renew_certificate(self, app):
        """为单个申请执行续期"""
        try:
            # 调用 service 执行续期（复用手动执行逻辑）
            from app.modules.acme.services import ApplicationService
            service = ApplicationService(engine)
            logger.info(f"▶️ 开始执行 {json.dumps(app.domains)} 证书续期任务:")
            service.execute(app.id, triggered_by="system")

        except Exception as e:
            logger.error(f"续期失败 {app.id}: {e}")
            # 可以记录失败，下次重试

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
