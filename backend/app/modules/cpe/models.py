"""
CPE 模块 - 数据模型

烽火 5G CPE 路由器管理
"""

from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, Text, Float
from app.core.db.database import metadata

# CPE 配置表
cpe_config_table = Table(
    "cpe_config",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False, comment="配置名称"),
    Column("host", String(255), nullable=False, comment="CPE 地址"),
    Column("username", String(100), nullable=False, default="admin", comment="用户名"),
    Column("password", String(255), nullable=False, comment="密码"),
    Column("is_active", Boolean, default=True, comment="是否启用"),
    Column("auto_monitor", Boolean, default=False, comment="自动监控短信"),
    Column("check_interval", Float, default=3.0, comment="检查间隔(秒)"),
    # 通知配置
    Column("bark_key", String(255), comment="Bark 推送 Key"),
    Column("bark_server", String(255), default="https://api.day.app", comment="Bark 服务器"),
    Column("feishu_webhook", String(500), comment="飞书 Webhook URL"),
    Column("webhook_url", String(500), comment="自定义 Webhook URL"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"),
    sqlite_autoincrement=True,
)

# 短信记录表
cpe_sms_table = Table(
    "cpe_sms",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("config_id", Integer, nullable=False, comment="配置 ID"),
    Column("sms_id", String(100), nullable=False, comment="短信 ID"),
    Column("phone", String(50), comment="短信号码"),
    Column("content", Text, comment="短信内容"),
    Column("time", String(50), comment="接收时间"),
    Column("is_read", Boolean, default=False, comment="是否已读"),
    Column("is_sent", Boolean, default=False, comment="是否发送"),
    Column("notified", Boolean, default=False, comment="是否已通知"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    sqlite_autoincrement=True,
)

__all__ = ["cpe_config_table", "cpe_sms_table"]
