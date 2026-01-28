import httpx
import asyncio
import json
from typing import Dict, Any, Optional
from sqlalchemy import select

from app.core.database import engine
from app.modules.notify.models import notification_services_table, notification_settings_table


class NotificationError(Exception):
    """通知发送异常"""
    pass

async def send_wecom_message(config: Dict[str, Any], title: str, content: str) -> bool:
    """企业微信通知"""
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "msgtype": "text",
                "text": {"content": f"{title}\n\n{content}"}
            }
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        print(f"企业微信发送失败: {e}")
        return False

async def send_bark_message(config: Dict[str, Any], title: str, content: str) -> bool:
    """Bark 通知"""
    bark_url = config.get("bark_url")
    if not bark_url:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # URL 编码处理
            import urllib.parse
            encoded_title = urllib.parse.quote(title)
            encoded_content = urllib.parse.quote(content)
            url = f"{bark_url.rstrip('/')}/{encoded_title}/{encoded_content}"
            resp = await client.get(url)
            return resp.status_code == 200
    except Exception as e:
        print(f"Bark 发送失败: {e}")
        return False

# 支持更多服务（可扩展）
SERVICE_HANDLERS = {
    "wecom": send_wecom_message,
    "bark": send_bark_message,
    # "dingtalk": send_dingtalk_message,
    # "email": send_email_message,
}

async def send_test_notification(service_type: str, config: Dict[str, Any]) -> bool:
    """发送测试通知"""
    handler = SERVICE_HANDLERS.get(service_type)
    if not handler:
        raise NotificationError(f"不支持的通知类型: {service_type}")

    title = "🔔 测试通知"
    content = "这是来自 ToolsPlus 的测试消息！"
    return await handler(config, title, content)

async def get_default_notification_service():
    """获取默认通知服务配置"""
    with engine.connect() as conn:
        # 获取默认服务ID
        settings_stmt = select(notification_settings_table).where(notification_settings_table.c.id == 1)
        settings = conn.execute(settings_stmt).mappings().first()

        if not settings or not settings["default_service_id"]:
            return None

        # 获取默认服务详情
        service_stmt = select(notification_services_table).where(
            notification_services_table.c.id == settings["default_service_id"],
            notification_services_table.c.is_enabled == True
        )
        service = conn.execute(service_stmt).mappings().first()

        if not service:
            return None

        return {
            "service_type": service["service_type"],
            "config": json.loads(service["config"]) if service["config"] else {}
        }

async def send_job_notification(job_name: str, node_name: str, status: str, execution_time: str):
    """发送任务完成通知（使用全局默认服务）"""
    try:
        # 获取默认服务
        service = await get_default_notification_service()
        if not service:
            print("无可用的默认通知服务")
            return False

        # 构建通知内容
        status_emoji = {"success": "✅", "failed": "❌", "cancelled": "⚠️"}
        emoji = status_emoji.get(status, "ℹ️")

        title = f"{emoji} 任务执行结果"
        content = f"""任务名称: {job_name}
节点名称: {node_name}
执行状态: {status}
完成时间: {execution_time}"""

        # 发送通知
        handler = SERVICE_HANDLERS.get(service["service_type"])
        if not handler:
            raise NotificationError(f"不支持的通知类型: {service['service_type']}")

        success = await handler(service["config"], title, content)
        if not success:
            raise NotificationError("通知发送失败")

        return True

    except Exception as e:
        print(f"发送通知异常: {e}")
        return False
