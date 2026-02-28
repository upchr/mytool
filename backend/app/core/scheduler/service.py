# app/core/scheduler/service.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from typing import Dict, List, Optional, Type, Any
import logging
from datetime import datetime

from .base import JobProvider, JobInfo, JobEvent

# 关闭 APScheduler 日志
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class SchedulerService:
    """通用定时任务调度服务"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.providers: Dict[str, JobProvider] = {}  # module_name -> provider
        self.job_ids: set = set()  # 所有已调度任务的ID
        self.event_handlers: Dict[str, list] = {}  # 事件处理器

        # 配置 jobstores
        self.scheduler.add_jobstore(MemoryJobStore(), 'default')

    def register_provider(self, provider: JobProvider) -> None:
        """注册任务提供者"""
        module_name = provider.get_module_name()
        if module_name in self.providers:
            logger.warning(f"模块 {module_name} 已存在，将被覆盖")
        self.providers[module_name] = provider
        logger.info(f"✅ 已注册任务提供者: {module_name}")

    def unregister_provider(self, module_name: str) -> None:
        """注销任务提供者"""
        if module_name in self.providers:
            # 移除该模块的所有任务
            for job_id in list(self.job_ids):
                if job_id.startswith(f"{module_name}:"):
                    self.remove_job(job_id)
            del self.providers[module_name]
            logger.info(f"✅ 已注销任务提供者: {module_name}")

    def start(self) -> None:
        """启动调度器"""
        self.load_all_jobs()
        self.scheduler.start()
        logger.info("✅ 定时任务调度器已启动")

    def shutdown(self) -> None:
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("⏹️ 定时任务调度器已停止")

    def load_all_jobs(self) -> None:
        """从所有注册的提供者加载任务"""
        for module_name, provider in self.providers.items():
            try:
                jobs = provider.get_enabled_jobs()
                for job_info in jobs:
                    self.add_job(job_info)
            except Exception as e:
                logger.error(f"❌ 从模块 {module_name} 加载任务失败: {e}")

    def add_job(self, job_info: JobInfo) -> bool:
        """添加单个任务到调度器"""
        # 使用 module:job_id 作为唯一标识
        full_job_id = f"{job_info.module}:{job_info.job_id}"

        if full_job_id in self.job_ids:
            logger.debug(f"任务 {full_job_id} 已存在，跳过")
            return False

        if not job_info.enabled:
            logger.debug(f"任务 {full_job_id} 未启用，跳过")
            return False

        try:
            # 创建 CronTrigger
            trigger = CronTrigger.from_crontab(job_info.schedule)

            # 添加到调度器
            self.scheduler.add_job(
                func=self._execute_job_wrapper,
                trigger=trigger,
                args=[job_info],
                id=full_job_id,
                name=job_info.name,
                replace_existing=True
            )
            self.job_ids.add(full_job_id)

            # 触发事件
            self._trigger_event(JobEvent.JOB_ADDED, job_info)

            # 调用提供者的回调
            if job_info.module in self.providers:
                self.providers[job_info.module].on_job_added(job_info)

            logger.info(f"📅 已添加定时任务: {job_info.name} ({job_info.schedule})")
            return True

        except Exception as e:
            logger.error(f"❌ 添加任务失败 {job_info.name}: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        if job_id in self.job_ids:
            try:
                self.scheduler.remove_job(job_id)
                self.job_ids.remove(job_id)

                # 获取模块和任务ID
                module, original_job_id = job_id.split(':', 1)

                # 创建 JobInfo 用于回调
                job_info = JobInfo(
                    job_id=original_job_id,
                    name="",
                    schedule="",
                    module=module
                )

                # 触发事件
                self._trigger_event(JobEvent.JOB_REMOVED, job_info)

                # 调用提供者的回调
                if module in self.providers:
                    self.providers[module].on_job_removed(job_info)

                logger.info(f"🗑️ 已移除定时任务: {job_id}")
                return True
            except Exception as e:
                logger.error(f"❌ 移除任务失败 {job_id}: {e}")
                return False
        return False

    def _execute_job_wrapper(self, job_info: JobInfo) -> None:
        """执行任务的包装函数"""
        module = job_info.module
        job_id = job_info.job_id
        job_name = job_info.name

        logger.info(f"▶️ 开始执行任务 {module}:{job_id} ({job_name})")

        try:
            if module not in self.providers:
                raise Exception(f"模块 {module} 未注册")

            provider = self.providers[module]
            result = provider.execute_job(job_info)

            # 触发事件
            self._trigger_event(JobEvent.JOB_EXECUTED, job_info, result)

            # 调用提供者的回调
            provider.on_job_executed(job_info, result, None)

            logger.info(f"✅ 任务执行成功 {module}:{job_id} ({job_name})")

        except Exception as e:
            logger.error(f"❌ 任务执行失败 {module}:{job_id} ({job_name}): {e}")

            # 触发事件
            self._trigger_event(JobEvent.JOB_FAILED, job_info, str(e))

            # 调用提供者的回调
            if module in self.providers:
                self.providers[module].on_job_executed(job_info, None, e)

    def on(self, event_type: str, handler) -> None:
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def _trigger_event(self, event_type: str, job_info: JobInfo, data: Any = None) -> None:
        """触发事件"""
        event = JobEvent(event_type, job_info, data)
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")

    def get_all_jobs(self) -> List[Dict]:
        """获取所有任务信息"""
        jobs = []
        for job_id in self.job_ids:
            job = self.scheduler.get_job(job_id)
            if job:
                jobs.append({
                    'id': job_id,
                    'name': job.name,
                    'next_run': job.next_run_time,
                    'schedule': str(job.trigger)
                })
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict]:
        """获取单个任务信息"""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job_id,
                'name': job.name,
                'next_run': job.next_run_time,
                'schedule': str(job.trigger)
            }
        return None

    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"⏸️ 已暂停任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 暂停任务失败 {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"▶️ 已恢复任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 恢复任务失败 {job_id}: {e}")
            return False

    def run_job_now(self, job_id: str) -> bool:
        """立即执行任务"""
        try:
            self.scheduler.modify_job(job_id, next_run_time=datetime.now())
            logger.info(f"⚡ 已触发立即执行: {job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 立即执行失败 {job_id}: {e}")
            return False


# 全局调度器实例
scheduler_service = SchedulerService()
