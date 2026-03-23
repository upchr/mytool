"""
CPE 模块 - 业务逻辑层
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select
from app.core.db.database import get_engine

from .models import cpe_config_table, cpe_sms_table
from .lib.client import CPEClient

logger = logging.getLogger(__name__)

# 全局监控器
_monitor_thread: Optional[threading.Thread] = None
_monitor_running = False
_current_config: Optional[Dict[str, Any]] = None


class CPEConfigService:
    """CPE 配置服务"""

    def __init__(self, engine):
        self.engine = engine
        self.table = cpe_config_table

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建配置"""
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        query = self.table.insert().values(data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return self.get_by_id(result.inserted_primary_key[0])

    def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新配置"""
        data["updated_at"] = datetime.now()

        query = self.table.update().where(self.table.c.id == id).values(data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return self.get_by_id(id) if result.rowcount > 0 else None

    def delete(self, id: int) -> bool:
        """删除配置"""
        query = self.table.delete().where(self.table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取配置"""
        query = select(self.table).where(self.table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None

    def get_all(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """获取所有配置"""
        query = select(self.table)
        if active_only:
            query = query.where(self.table.c.is_active == True)

        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result.fetchall()]

    def toggle_status(self, id: int, is_active: bool) -> bool:
        """切换启用状态"""
        query = self.table.update().where(self.table.c.id == id).values(
            is_active=is_active,
            updated_at=datetime.now()
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0


class CPESMSService:
    """CPE 短信服务"""

    def __init__(self, engine):
        self.engine = engine
        self.table = cpe_sms_table

    def create(self, data: Dict[str, Any]) -> int:
        """创建短信记录"""
        query = self.table.insert().values(data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]

    def get_list(self, config_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取短信列表"""
        query = select(self.table).where(self.table.c.config_id == config_id).order_by(self.table.c.created_at.desc()).limit(limit)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result.fetchall()]

    def mark_notified(self, id: int) -> bool:
        """标记为已通知"""
        query = self.table.update().where(self.table.c.id == id).values(notified=True)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0


class CPEMonitorService:
    """CPE 监控服务"""

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """获取监控状态"""
        global _monitor_running, _current_config

        return {
            "running": _monitor_running,
            "config_id": _current_config.get("id") if _current_config else None,
            "config_name": _current_config.get("name") if _current_config else None,
            "check_interval": _current_config.get("check_interval", 3.0) if _current_config else 3.0
        }

    @staticmethod
    def auto_start_monitor(engine) -> bool:
        """
        系统启动时自动启动监控
        
        检查所有 auto_monitor=True 且 is_active=True 的配置，启动第一个
        """
        global _monitor_running, _current_config
        
        if _monitor_running:
            return False
        
        config_service = CPEConfigService(engine)
        configs = config_service.get_all(active_only=True)
        
        # 找到第一个启用自动监控的配置
        for config in configs:
            if config.get("auto_monitor"):
                logger.info(f"自动启动 CPE 监控: {config['name']}")
                return CPEMonitorService.start_monitor(config)
        
        return False

    @staticmethod
    def start_monitor(config: Dict[str, Any]) -> bool:
        """启动监控"""
        global _monitor_thread, _monitor_running, _current_config

        if _monitor_running:
            return False

        _current_config = config
        _monitor_running = True

        def monitor_loop():
            global _monitor_running

            client = CPEClient(
                config["host"],
                config["username"],
                config["password"]
            )

            engine = get_engine()
            sms_service = CPESMSService(engine)

            while _monitor_running:
                try:
                    # 登录
                    if not client.is_logged_in():
                        success, msg = client.login()
                        if not success:
                            logger.warning(f"登录失败: {msg}")
                            time.sleep(60)
                            continue

                    # 心跳
                    if not client.heartbeat():
                        logger.warning("心跳失败")
                        time.sleep(10)
                        continue

                    # 检查新短信
                    if client.get_new_sms_flag():
                        sms_list = client.get_unread_sms()
                        for sms in sms_list:
                            # 保存短信
                            sms_service.create({
                                "config_id": config["id"],
                                "sms_id": sms["id"],
                                "phone": sms["phone"],
                                "content": sms["content"],
                                "time": sms["time"],
                                "is_read": sms["is_read"],
                                "is_sent": sms["is_sent"],
                                "notified": False
                            })

                            # 发送通知
                            CPEMonitorService._send_notification(config, sms)

                            # 标记已读
                            client.mark_sms_read(sms["id"])

                    time.sleep(config.get("check_interval", 3.0))

                except Exception as e:
                    logger.error(f"监控出错: {e}")
                    time.sleep(10)

            client.logout()

        _monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        _monitor_thread.start()

        return True

    @staticmethod
    def stop_monitor() -> bool:
        """停止监控"""
        global _monitor_running, _current_config

        _monitor_running = False
        _current_config = None

        return True

    @staticmethod
    def _send_notification(config: Dict[str, Any], sms: Dict[str, Any]):
        """发送通知"""
        import urllib.request
        import urllib.parse
        import json

        title = f"From: {sms['phone']}"
        content = f"{sms['content']}\n\nTime: {sms['time']}"

        # Bark 通知
        if config.get("bark_key"):
            try:
                escaped_title = urllib.parse.quote(title)
                escaped_content = urllib.parse.quote(content)
                url = f"{config.get('bark_server', 'https://api.day.app')}/{config['bark_key']}/{escaped_title}/{escaped_content}"
                urllib.request.urlopen(url, timeout=10)
            except Exception as e:
                logger.error(f"Bark 通知失败: {e}")

        # 飞书 Webhook
        if config.get("feishu_webhook"):
            try:
                data = {
                    "msg_type": "text",
                    "content": {"text": f"【{title}】\n\n{content}"}
                }
                req = urllib.request.Request(
                    config["feishu_webhook"],
                    data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                logger.error(f"飞书通知失败: {e}")

        # 自定义 Webhook
        if config.get("webhook_url"):
            try:
                data = {"title": title, "content": content}
                req = urllib.request.Request(
                    config["webhook_url"],
                    data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                logger.error(f"Webhook 通知失败: {e}")


class CPEClientService:
    """CPE 客户端服务（直接操作）"""

    @staticmethod
    def test_connection(host: str, username: str, password: str) -> Dict[str, Any]:
        """测试连接"""
        client = CPEClient(host, username, password)
        success, msg = client.login()

        result = {"success": success, "message": msg}

        if success:
            try:
                # 获取设备信息
                device_info = client.get_device_info()
                result["device_info"] = {
                    "model_name": device_info.get("model_name", ""),
                    "mac_address": device_info.get("brmac", "")
                }
            except Exception as e:
                result["error"] = str(e)
            finally:
                client.logout()

        return result

    @staticmethod
    def get_device_info(host: str, username: str, password: str) -> Dict[str, Any]:
        """获取设备信息"""
        client = CPEClient(host, username, password)
        success, msg = client.login()

        if not success:
            return {"success": False, "message": msg}

        try:
            # 基本信息
            device_info = client.get_device_info()

            # 详细信息
            details = client.get_device_details()

            # 温度
            temp = client.get_temperature()

            # 运行时间
            uptime = client.get_uptime()

            return {
                "success": True,
                "data": {
                    "product_name": "5G CPE",
                    "model_name": device_info.get("model_name", "") or details.get("ModelName", ""),
                    "serial_number": details.get("SerialNumber", ""),
                    "mac_address": device_info.get("brmac", ""),
                    "software_version": details.get("SoftwareVersion", ""),
                    "hardware_version": details.get("HardwareVersion", ""),
                    "uptime": uptime,
                    "temperature": {
                        "temp_5g": temp.get("temp_5g", 0),
                        "temp_4g": temp.get("temp_4g"),
                        "unit": "℃"
                    }
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

        finally:
            client.logout()

    @staticmethod
    def get_sms_list(host: str, username: str, password: str, limit: int = 20) -> Dict[str, Any]:
        """获取短信列表"""
        client = CPEClient(host, username, password)
        success, msg = client.login()

        if not success:
            return {"success": False, "message": msg}

        try:
            sms_list = client.get_sms_list()

            return {
                "success": True,
                "total": len(sms_list),
                "items": sms_list[:limit]
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

        finally:
            client.logout()
