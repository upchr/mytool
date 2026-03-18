# app/modules/plugin/plugin_base.py
"""
插件基类和权限定义

所有插件都应继承 BasePlugin
"""
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


def require_permission(permission: str):
    """
    权限检查装饰器
    
    Args:
        permission: 需要的权限
    """
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
    """
    插件基类
    
    所有插件都必须继承此类并实现必要的方法
    """
    
    # 插件元信息（子类必须覆盖）
    plugin_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    plugin_type: str = ""  # notification/executor/datasource
    icon: str = "📦"
    
    # 插件声明的权限
    required_permissions: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 granted_permissions: Optional[Set[str]] = None):
        """
        初始化插件
        
        Args:
            config: 插件配置
            granted_permissions: 授予的权限集合
        """
        self.config = config or {}
        self._permissions = granted_permissions or set()
        self.logger = logging.getLogger(f"plugin.{self.plugin_id}")
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        获取配置项 Schema
        
        Returns:
            JSON Schema 格式的配置定义
        """
        pass
    
    def on_load(self):
        """插件加载时调用"""
        self.logger.info(f"插件加载: {self.name}")
    
    def on_unload(self):
        """插件卸载时调用"""
        self.logger.info(f"插件卸载: {self.name}")
    
    def set_logger(self, logger):
        """设置日志器"""
        self.logger = logger


# ========== 通知类插件基类 ==========

class NotificationPlugin(BasePlugin):
    """通知类插件基类"""
    
    plugin_type = "notification"
    
    @abstractmethod
    def send(self, title: str, content: str, **kwargs) -> bool:
        """
        发送通知
        
        Args:
            title: 标题
            content: 内容
            **kwargs: 额外参数
        
        Returns:
            是否发送成功
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook 地址"
                }
            }
        }


# ========== 执行器类插件基类 ==========

class ExecutorPlugin(BasePlugin):
    """执行器类插件基类"""
    
    plugin_type = "executor"
    
    @abstractmethod
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            **kwargs: 额外参数
        
        Returns:
            执行结果
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "integer",
                    "title": "超时时间（秒）",
                    "default": 300
                }
            }
        }


# ========== 内置插件定义 ==========

class FeishuNotificationPlugin(NotificationPlugin):
    """飞书群机器人通知插件"""
    
    plugin_id = "notification-feishu"
    name = "飞书通知"
    author = "ToolsPlus Team"
    description = "通过飞书群机器人发送通知"
    icon = "📘"
    
    def send(self, title: str, content: str, **kwargs) -> bool:
        """发送飞书通知"""
        import requests
        
        url = self.config.get("webhook_url")
        if not url:
            self.logger.error("飞书 Webhook 未配置")
            return False
        
        try:
            data = {
                "msg_type": "interactive",
                "card": {
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "content": content,
                                "tag": "lark_md"
                            }
                        }
                    ],
                    "header": {
                        "title": {
                            "content": title,
                            "tag": "plain_text"
                        },
                        "template": "blue"
                    }
                }
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            self.logger.info(f"飞书通知发送成功: {title}")
            return True
        except Exception as e:
            self.logger.error(f"飞书通知发送失败: {e}")
            return False


class DingtalkNotificationPlugin(NotificationPlugin):
    """钉钉群机器人通知插件"""
    
    plugin_id = "notification-dingtalk"
    name = "钉钉通知"
    author = "ToolsPlus Team"
    description = "通过钉钉群机器人发送通知"
    icon = "📎"
    
    def send(self, title: str, content: str, **kwargs) -> bool:
        """发送钉钉通知"""
        import requests
        
        url = self.config.get("webhook_url")
        secret = self.config.get("secret")
        
        if not url:
            self.logger.error("钉钉 Webhook 未配置")
            return False
        
        try:
            # 如果有 secret，加签
            if secret:
                import time
                import hmac
                import hashlib
                import base64
                import urllib.parse
                
                timestamp = str(round(time.time() * 1000))
                secret_enc = secret.encode("utf-8")
                string_to_sign = f"{timestamp}\n{secret}"
                string_to_sign_enc = string_to_sign.encode("utf-8")
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, 
                                     digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                url = f"{url}&timestamp={timestamp}&sign={sign}"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"### {title}\n\n{content}"
                }
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            self.logger.info(f"钉钉通知发送成功: {title}")
            return True
        except Exception as e:
            self.logger.error(f"钉钉通知发送失败: {e}")
            return False


class WecomNotificationPlugin(NotificationPlugin):
    """企业微信通知插件"""
    
    plugin_id = "notification-wecom"
    name = "企业微信通知"
    author = "ToolsPlus Team"
    description = "通过企业微信机器人发送通知"
    icon = "💬"
    
    def send(self, title: str, content: str, **kwargs) -> bool:
        """发送企业微信通知"""
        import requests
        
        url = self.config.get("webhook_url")
        if not url:
            self.logger.error("企业微信 Webhook 未配置")
            return False
        
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n\n{content}"
                }
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            self.logger.info(f"企业微信通知发送成功: {title}")
            return True
        except Exception as e:
            self.logger.error(f"企业微信通知发送失败: {e}")
            return False


class BarkNotificationPlugin(NotificationPlugin):
    """Bark iOS 通知插件"""
    
    plugin_id = "notification-bark"
    name = "Bark 通知"
    author = "ToolsPlus Team"
    description = "通过 Bark 发送 iOS 推送"
    icon = "🍎"
    
    def send(self, title: str, content: str, **kwargs) -> bool:
        """发送 Bark 通知"""
        import requests
        
        server = self.config.get("server", "https://api.day.app")
        key = self.config.get("key")
        
        if not key:
            self.logger.error("Bark Key 未配置")
            return False
        
        try:
            url = f"{server}/{key}/{title}/{content}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Bark 通知发送成功: {title}")
            return True
        except Exception as e:
            self.logger.error(f"Bark 通知发送失败: {e}")
            return False


class LocalExecutorPlugin(ExecutorPlugin):
    """本地执行器插件"""
    
    plugin_id = "executor-local"
    name = "本地执行器"
    author = "ToolsPlus Team"
    description = "在本地执行 Shell 命令"
    icon = "💻"
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """执行本地命令"""
        import subprocess
        
        timeout = kwargs.get("timeout", self.config.get("timeout", 300))
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": f"执行超时（{timeout}秒）"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


# ========== 插件注册表 ==========

BUILTIN_PLUGINS = [
    FeishuNotificationPlugin,
    DingtalkNotificationPlugin,
    WecomNotificationPlugin,
    BarkNotificationPlugin,
    LocalExecutorPlugin,
]


def get_builtin_plugins() -> List[type]:
    """获取所有内置插件类"""
    return BUILTIN_PLUGINS


def get_plugin_by_id(plugin_id: str) -> Optional[type]:
    """根据 ID 获取插件类"""
    for plugin_class in BUILTIN_PLUGINS:
        if plugin_class.plugin_id == plugin_id:
            return plugin_class
    return None


__all__ = [
    "BasePlugin",
    "NotificationPlugin", 
    "ExecutorPlugin",
    "PluginPermission",
    "require_permission",
    "BUILTIN_PLUGINS",
    "get_builtin_plugins",
    "get_plugin_by_id",
    "FeishuNotificationPlugin",
    "DingtalkNotificationPlugin",
    "WecomNotificationPlugin",
    "BarkNotificationPlugin",
    "LocalExecutorPlugin",
]
