from .plugin_base import NotificationPlugin, ExecutorPlugin, StoragePlugin, AIEnginePlugin
from typing import Dict, Any, List
import requests
import json


# ============== 内置通知渠道插件 ==============

class WebhookNotificationPlugin(NotificationPlugin):
    """自定义Webhook通知插件"""
    plugin_id = "notification-webhook"
    name = "自定义Webhook"
    description = "通过自定义Webhook发送通知"
    category = "通知渠道"
    icon = "🔗"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook地址",
                    "required": True
                },
                "method": {
                    "type": "string",
                    "title": "请求方法",
                    "enum": ["POST", "GET"],
                    "default": "POST"
                },
                "content_type": {
                    "type": "string",
                    "title": "Content-Type",
                    "default": "application/json"
                }
            }
        }

    def send(self, title: str, content: str, **kwargs) -> bool:
        url = self.config.get("webhook_url")
        method = self.config.get("method", "POST")
        content_type = self.config.get("content_type", "application/json")

        if not url:
            self.log("Webhook地址未配置", "error")
            return False

        try:
            if content_type == "application/json":
                data = {"title": title, "content": content, **kwargs}
                if method == "POST":
                    requests.post(url, json=data, timeout=10)
                else:
                    requests.get(url, params=data, timeout=10)
            else:
                if method == "POST":
                    requests.post(url, data={"title": title, "content": content}, timeout=10)
                else:
                    requests.get(url, params={"title": title, "content": content}, timeout=10)
            self.log(f"通知发送成功: {title}")
            return True
        except Exception as e:
            self.log(f"通知发送失败: {e}", "error")
            return False


class BarkNotificationPlugin(NotificationPlugin):
    """Bark通知插件（iOS）"""
    plugin_id = "notification-bark"
    name = "Bark"
    description = "通过Bark发送iOS推送通知"
    category = "通知渠道"
    icon = "📱"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bark_key": {
                    "type": "string",
                    "title": "Bark Key",
                    "required": True
                },
                "bark_url": {
                    "type": "string",
                    "title": "Bark服务器地址",
                    "default": "https://api.day.app"
                }
            }
        }

    def send(self, title: str, content: str, **kwargs) -> bool:
        key = self.config.get("bark_key")
        base_url = self.config.get("bark_url", "https://api.day.app")

        if not key:
            self.log("Bark Key未配置", "error")
            return False

        try:
            url = f"{base_url}/{key}/{title}/{content}"
            requests.get(url, timeout=10)
            self.log(f"Bark通知发送成功: {title}")
            return True
        except Exception as e:
            self.log(f"Bark通知发送失败: {e}", "error")
            return False


class WecomNotificationPlugin(NotificationPlugin):
    """企业微信群通知插件"""
    plugin_id = "notification-wecom"
    name = "企业微信"
    description = "通过企业微信群机器人发送通知"
    category = "通知渠道"
    icon = "🤖"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook地址",
                    "required": True
                }
            }
        }

    def send(self, title: str, content: str, **kwargs) -> bool:
        url = self.config.get("webhook_url")

        if not url:
            self.log("企业微信Webhook未配置", "error")
            return False

        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n\n{content}"
                }
            }
            requests.post(url, json=data, timeout=10)
            self.log(f"企业微信通知发送成功: {title}")
            return True
        except Exception as e:
            self.log(f"企业微信通知发送失败: {e}", "error")
            return False


class FeishuNotificationPlugin(NotificationPlugin):
    """飞书群机器人通知插件"""
    plugin_id = "notification-feishu"
    name = "飞书"
    description = "通过飞书群机器人发送通知"
    category = "通知渠道"
    icon = "📘"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook地址",
                    "required": True
                }
            }
        }

    def send(self, title: str, content: str, **kwargs) -> bool:
        url = self.config.get("webhook_url")

        if not url:
            self.log("飞书Webhook未配置", "error")
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
            requests.post(url, json=data, timeout=10)
            self.log(f"飞书通知发送成功: {title}")
            return True
        except Exception as e:
            self.log(f"飞书通知发送失败: {e}", "error")
            return False


class DingtalkNotificationPlugin(NotificationPlugin):
    """钉钉群机器人通知插件"""
    plugin_id = "notification-dingtalk"
    name = "钉钉"
    description = "通过钉钉群机器人发送通知"
    category = "通知渠道"
    icon = "📎"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook地址",
                    "required": True
                },
                "secret": {
                    "type": "string",
                    "title": "加签密钥（可选）",
                    "required": False
                }
            }
        }

    def send(self, title: str, content: str, **kwargs) -> bool:
        url = self.config.get("webhook_url")
        secret = self.config.get("secret")

        if not url:
            self.log("钉钉Webhook未配置", "error")
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
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                url = f"{url}&timestamp={timestamp}&sign={sign}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"### {title}\n\n{content}"
                }
            }
            requests.post(url, json=data, timeout=10)
            self.log(f"钉钉通知发送成功: {title}")
            return True
        except Exception as e:
            self.log(f"钉钉通知发送失败: {e}", "error")
            return False


# ============== 内置执行器插件 ==============

class LocalExecutorPlugin(ExecutorPlugin):
    """本地Shell执行器插件"""
    plugin_id = "executor-local"
    name = "本地Shell"
    description = "在本地执行Shell命令"
    category = "执行器"
    icon = "💻"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "number",
                    "title": "超时时间（秒）",
                    "default": 300
                },
                "cwd": {
                    "type": "string",
                    "title": "工作目录",
                    "default": ""
                }
            }
        }

    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        import subprocess
        import os

        timeout = self.config.get("timeout", 300)
        cwd = self.config.get("cwd") or os.getcwd()

        try:
            self.log(f"执行命令: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "output": "",
                "error": f"执行超时（{timeout}秒）",
                "returncode": -1
            }
        except Exception as e:
            self.log(f"执行失败: {e}", "error")
            return {
                "status": "failed",
                "output": "",
                "error": str(e),
                "returncode": -1
            }


# ============== 内置存储插件 ==============

class LocalStoragePlugin(StoragePlugin):
    """本地存储插件"""
    plugin_id = "storage-local"
    name = "本地存储"
    description = "本地文件系统存储"
    category = "存储"
    icon = "💾"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_path": {
                    "type": "string",
                    "title": "基础路径",
                    "default": "/data/storage"
                }
            }
        }

    def upload(self, local_path: str, remote_path: str, **kwargs) -> bool:
        import shutil
        import os

        base_path = self.config.get("base_path", "/data/storage")
        dest_path = os.path.join(base_path, remote_path.lstrip("/"))

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(local_path, dest_path)
            self.log(f"文件上传成功: {local_path} -> {dest_path}")
            return True
        except Exception as e:
            self.log(f"文件上传失败: {e}", "error")
            return False

    def download(self, remote_path: str, local_path: str, **kwargs) -> bool:
        import shutil
        import os

        base_path = self.config.get("base_path", "/data/storage")
        src_path = os.path.join(base_path, remote_path.lstrip("/"))

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            shutil.copy2(src_path, local_path)
            self.log(f"文件下载成功: {src_path} -> {local_path}")
            return True
        except Exception as e:
            self.log(f"文件下载失败: {e}", "error")
            return False

    def delete(self, remote_path: str, **kwargs) -> bool:
        import os

        base_path = self.config.get("base_path", "/data/storage")
        file_path = os.path.join(base_path, remote_path.lstrip("/"))

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.log(f"文件删除成功: {file_path}")
            return True
        except Exception as e:
            self.log(f"文件删除失败: {e}", "error")
            return False


# ============== 获取内置插件列表 ==============

def get_builtin_plugins():
    """获取所有内置插件"""
    return [
        WebhookNotificationPlugin,
        BarkNotificationPlugin,
        WecomNotificationPlugin,
        FeishuNotificationPlugin,
        DingtalkNotificationPlugin,
        LocalExecutorPlugin,
        LocalStoragePlugin,
    ]
