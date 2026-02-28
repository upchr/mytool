from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JobInfo:
    """任务信息类"""
    def __init__(self,
                 job_id: str,
                 name: str,
                 schedule: str,
                 module: str,
                 enabled: bool = True,
                 params: Optional[Dict] = None,
                 description: str = ""):
        self.job_id = job_id
        self.name = name
        self.schedule = schedule  # cron 表达式
        self.module = module
        self.enabled = enabled
        self.params = params or {}
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class JobProvider(ABC):
    """任务提供者抽象基类"""

    @abstractmethod
    def get_module_name(self) -> str:
        """返回模块名称"""
        pass

    @abstractmethod
    def get_all_jobs(self) -> List[JobInfo]:
        """获取所有任务"""
        pass

    @abstractmethod
    def get_enabled_jobs(self) -> List[JobInfo]:
        """获取所有启用的任务"""
        pass

    @abstractmethod
    def execute_job(self, job_info: JobInfo) -> Any:
        """执行任务"""
        pass

    @abstractmethod
    def on_job_added(self, job_info: JobInfo) -> None:
        """任务添加时的回调"""
        pass

    @abstractmethod
    def on_job_removed(self, job_info: JobInfo) -> None:
        """任务移除时的回调"""
        pass

    @abstractmethod
    def on_job_executed(self, job_info: JobInfo, result: Any, error: Optional[Exception]) -> None:
        """任务执行后的回调"""
        pass


class JobEvent:
    """任务事件类"""
    JOB_ADDED = "job_added"
    JOB_REMOVED = "job_removed"
    JOB_EXECUTED = "job_executed"
    JOB_FAILED = "job_failed"
    JOB_SKIPPED = "job_skipped"

    def __init__(self, event_type: str, job_info: JobInfo, data: Any = None):
        self.event_type = event_type
        self.job_info = job_info
        self.data = data
        self.timestamp = datetime.now()
