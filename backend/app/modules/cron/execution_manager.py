from threading import Event
from typing import Dict

class ExecutionCancelledError(Exception):
    """任务被用户主动中断"""
    pass
class ExecutionManager:
    def __init__(self):
        # execution_id -> Event
        self.stop_events: Dict[int, Event] = {}

    def create_execution(self, execution_id: int):
        """创建执行任务的停止事件"""
        self.stop_events[execution_id] = Event()

    def stop_execution(self, execution_id: int):
        """触发停止事件"""
        if execution_id in self.stop_events:
            self.stop_events[execution_id].set()

    def should_stop(self, execution_id: int) -> bool:
        """检查是否应该停止"""
        if execution_id in self.stop_events:
            return self.stop_events[execution_id].is_set()
        return False

    def cleanup(self, execution_id: int):
        """清理资源"""
        if execution_id in self.stop_events:
            del self.stop_events[execution_id]

# 全局实例
execution_manager = ExecutionManager()
