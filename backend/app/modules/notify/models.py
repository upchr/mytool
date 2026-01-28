from sqlalchemy import Table, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry

from app.core.database import engine

# 使用 registry 替代已弃用的 declarative_base
mapper_registry = registry()
metadata = mapper_registry.metadata

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
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())
)

# 全局通知设置表
notification_settings_table = Table(
    "notification_settings",
    metadata,
    Column("id", Integer, primary_key=True, default=1),
    Column("default_service_id", Integer, ForeignKey("notification_services.id"), nullable=True),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())
)

def init_default_notification_services():
    """在应用启动时自动初始化默认通知服务"""
    with engine.begin() as conn:
        # 检查是否已存在数据
        count = conn.execute(select(func.count()).select_from(notification_services_table)).scalar()
        if count == 0:
            print("正在初始化默认通知服务...")

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

            print("✅ 默认通知服务初始化完成！")
        else:
            print("✅ 通知服务已存在，跳过初始化")

# ========== 创建表并初始化 ==========
# 在应用启动时调用
if __name__ != "__main__":
    metadata.create_all(engine, tables=[
        notification_services_table,
        notification_settings_table
    ])
    init_default_notification_services()


# 在现有任务表中添加 notify_enabled 字段
# 假设你已有 cron_jobs_table，添加以下字段：
# Column("notify_enabled", Boolean, default=False, nullable=False)
