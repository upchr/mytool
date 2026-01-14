from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from . import services, models
from sqlalchemy import select
from app.core.database import engine
import logging

# 关闭 APScheduler 日志（可选）
logging.getLogger('apscheduler').setLevel(logging.WARNING)

class CronJobScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_ids = set()  # 跟踪已调度的任务ID

    def start(self):
        """启动调度器并加载所有启用的任务"""
        self.load_all_jobs()
        self.scheduler.start()
        print("✅ 定时任务调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        print("⏹️ 定时任务调度器已停止")

    def load_all_jobs(self):
        """从数据库加载所有启用的定时任务"""
        with engine.connect() as conn:
            stmt = select(models.cron_jobs_table).where(
                models.cron_jobs_table.c.is_active == True
            )
            results = conn.execute(stmt).mappings().all()

            for job in results:
                self.add_job(job)

    def add_job(self, job):
        """添加单个任务到调度器"""
        if job['id'] in self.job_ids:
            return

        try:
            # 创建 CronTrigger
            trigger = CronTrigger.from_crontab(job['schedule'])

            # 添加到调度器
            self.scheduler.add_job(
                func=self._execute_job_task,
                trigger=trigger,
                args=[job['id'], job['name']],
                id=str(job['id']),
                name=job['name']
            )
            self.job_ids.add(job['id'])
            print(f"📅 已添加定时任务: {job['name']} ({job['schedule']})")
        except Exception as e:
            print(f"❌ 添加任务失败 {job['name']}: {e}")

    def remove_job(self, job_id, job_name):
        """移除任务"""
        if job_id in self.job_ids:
            self.scheduler.remove_job(str(job_id))
            self.job_ids.remove(job_id)
            print(f"🗑️ 已移除定时任务: {job_id} ({job_name})")

    def _execute_job_task(self, job_id, job_name):
        """实际执行任务的函数（被调度器调用）"""
        try:
            # 调用你的 execute_job 函数
            print(f"✅ 系统自动执行任务 {job_id} ({job_name})")
            services.execute_job(engine, job_id, triggered_by="system")
        except Exception as e:
            print(f"❌ 自动执行任务 {job_id} ({job_name}) 失败: {e}")

# 全局调度器实例
scheduler = CronJobScheduler()
