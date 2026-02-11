import logging
from linecache import cache

from sqlalchemy import Table, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func, select
from app.core.db.database import engine, metadata
from app.core.exception.exceptions import ServerException

logger = logging.getLogger(__name__)

# 通知服务配置表
notification_services_table = Table(
    "notification_services",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("service_type", String(20), nullable=False),      # wecom, bark, dingtalk, email
    Column("service_name", String(50), nullable=False),       # 显示名称
    Column("is_enabled", Boolean, default=False, nullable=False),
    Column("config", Text),                                  # JSON 配置
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
    sqlite_autoincrement=True,
)

# 全局通知设置表
notification_settings_table = Table(
    "notification_settings",
    metadata,
    Column("id", Integer, primary_key=True, default=1),
    Column("default_service_id", Integer, ForeignKey("notification_services.id"), nullable=True),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
    sqlite_autoincrement=True,
)

def init_default_notification_services():
    """在应用启动时自动初始化默认通知服务"""
    try:
        with engine.begin() as conn:
            # 检查是否已存在数据
            count = conn.execute(select(func.count()).select_from(notification_services_table)).scalar()
            if count == 0:
                logger.debug("🔧正在初始化默认通知服务...")
                # 插入默认服务
                default_services = [
                    {"service_type": "wecom", "service_name": "企业微信", "is_enabled": False},
                    {"service_type": "bark", "service_name": "Bark", "is_enabled": False},
                    {"service_type": "dingtalk", "service_name": "钉钉", "is_enabled": False},
                    {"service_type": "feishu", "service_name": "飞书", "is_enabled": False},
                    {"service_type": "email", "service_name": "邮件", "is_enabled": False}
                ]

                for service in default_services:
                    conn.execute(notification_services_table.insert().values(**service))

                # 初始化全局设置表
                settings_count = conn.execute(select(func.count()).select_from(notification_settings_table)).scalar()
                if settings_count == 0:
                    conn.execute(notification_settings_table.insert().values(id=1))
                logger.debug("默认通知服务初始化完成！")

            else:
                logger.debug("通知服务已存在，跳过初始化！")
    except Exception as e:
        detail = f"初始化消息数据失败: {str(e)}"
        logger.error(detail)
        raise ServerException(detail=detail)



__all__ = ["notification_services_table","notification_settings_table","init_default_notification_services"]
