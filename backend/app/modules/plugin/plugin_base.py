from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
import functools
import logging


class PluginPermission:
    """插件权限定义"""
    NETWORK = "network"           # 网络访问
    FILESYSTEM_READ = "fs_read"   # 文件系统读
    FILESYSTEM_WRITE = "fs_write" # 文件系统写
    PROCESS_EXEC = "process_exec" # 进程执行
    DATABASE = "database"          # 数据库访问
    NOTIFICATION = "notification"  # 发送通知
    SCHEDULE = "schedule"          # 调度任务
    CONFIG_READ = "config_read"    # 读取配置
    CONFIG_WRITE = "config_write"  # 写入配置


def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_permissions'):
                raise PermissionError(f"插件未配置权限: {permission}")
            if permission not in self._permissions:
                raise PermissionError(f"插件缺少权限: {permission}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class BasePlugin(ABC):
    """插件基类"""

    # 插件元数据
    plugin_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    author: str = "MyTool Team"
    description: str = ""
    plugin_type: str = ""  # notification/executor/datasource/trigger/storage/ai
    category: str = ""
    icon: str = ""

    # 插件声明需要的权限
    required_permissions: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None, granted_permissions: Optional[Set[str]] = None):
        self.config = config or {}
        self.logger = None
        self._permissions = granted_permissions or set()
        self._sandbox_context: Optional[Dict[str, Any]] = None

    def set_logger(self, logger):
        """设置日志器"""
        self.logger = logger

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(f"[{self.plugin_id}] {message}")

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema"""
        pass

    def on_load(self):
        """插件加载时调用"""
        pass

    def on_unload(self):
        """插件卸载时调用"""
        pass


# ============== 通知渠道插件基类 ==============

class NotificationPlugin(BasePlugin):
    """通知渠道插件基类"""

    plugin_type: str = "notification"

    @abstractmethod
    def send(self, title: str, content: str, **kwargs) -> bool:
        """
        发送通知

        Args:
            title: 通知标题
            content: 通知内容
            **kwargs: 额外参数

        Returns:
            是否发送成功
        """
        pass


# ============== 任务执行器插件基类 ==============

class ExecutorPlugin(BasePlugin):
    """任务执行器插件基类"""

    plugin_type: str = "executor"

    @abstractmethod
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行任务

        Args:
            command: 命令/脚本
            **kwargs: 额外参数

        Returns:
            执行结果: {status: success/failed, output: ..., error: ...}
        """
        pass


# ============== 数据源插件基类 ==============

class DataSourcePlugin(BasePlugin):
    """数据源插件基类"""

    plugin_type: str = "datasource"

    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass

    @abstractmethod
    def query(self, query_str: str, **kwargs) -> Any:
        """
        查询数据

        Args:
            query_str: 查询语句
            **kwargs: 额外参数

        Returns:
            查询结果
        """
        pass


# ============== 触发器插件基类 ==============

class TriggerPlugin(BasePlugin):
    """触发器插件基类"""

    plugin_type: str = "trigger"

    @abstractmethod
    def start(self):
        """启动触发器"""
        pass

    @abstractmethod
    def stop(self):
        """停止触发器"""
        pass

    def on_trigger(self, data: Dict[str, Any]):
        """触发事件回调"""
        pass


# ============== 存储插件基类 ==============

class StoragePlugin(BasePlugin):
    """存储插件基类"""

    plugin_type: str = "storage"

    @abstractmethod
    def upload(self, local_path: str, remote_path: str, **kwargs) -> bool:
        """
        上传文件

        Args:
            local_path: 本地路径
            remote_path: 远程路径
            **kwargs: 额外参数

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str, **kwargs) -> bool:
        """
        下载文件

        Args:
            remote_path: 远程路径
            local_path: 本地路径
            **kwargs: 额外参数

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def delete(self, remote_path: str, **kwargs) -> bool:
        """
        删除文件

        Args:
            remote_path: 远程路径
            **kwargs: 额外参数

        Returns:
            是否成功
        """
        pass


# ============== AI引擎插件基类 ==============

class AIEnginePlugin(BasePlugin):
    """AI引擎插件基类"""

    plugin_type: str = "ai"

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话

        Args:
            messages: 消息列表，如 [{"role": "user", "content": "你好"}]
            **kwargs: 额外参数

        Returns:
            AI回复内容
        """
        pass

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """
        文本补全

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Returns:
            补全结果
        """
        pass

    def get_embedding(self, text: str, **kwargs) -> List[float]:
        """
        获取文本向量嵌入（可选）

        Args:
            text: 文本
            **kwargs: 额外参数

        Returns:
            向量数组
        """
        raise NotImplementedError


# ============== 插件沙箱管理器 ==============

class PluginSandbox:
    """插件沙箱管理器 - 限制插件资源访问"""
    
    def __init__(self, plugin_id: str, allowed_dirs: Optional[List[str]] = None):
        self.plugin_id = plugin_id
        self.allowed_dirs = allowed_dirs or []
        self.logger = logging.getLogger(f"plugin_sandbox.{plugin_id}")
        self._operation_log: List[Dict] = []
    
    def log_operation(self, operation: str, details: Dict[str, Any]):
        """记录插件操作"""
        log_entry = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "operation": operation,
            "details": details
        }
        self._operation_log.append(log_entry)
        self.logger.debug(f"Plugin operation: {operation} - {details}")
    
    def can_access_file(self, path: str, mode: str = "r") -> bool:
        """检查是否可以访问文件"""
        import os
        norm_path = os.path.normpath(path)
        
        for allowed_dir in self.allowed_dirs:
            allowed_norm = os.path.normpath(allowed_dir)
            if norm_path.startswith(allowed_norm):
                self.log_operation("file_access", {"path": path, "mode": mode, "allowed": True})
                return True
        
        self.log_operation("file_access", {"path": path, "mode": mode, "allowed": False})
        return False
    
    def can_access_network(self, host: str, port: int = None) -> bool:
        """检查是否可以访问网络"""
        self.log_operation("network_access", {"host": host, "port": port})
        return True
    
    def get_operation_log(self, limit: int = 100) -> List[Dict]:
        """获取操作日志"""
        return self._operation_log[-limit:]
