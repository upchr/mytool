from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, func
from app.core.db.database import metadata

# 系统配置表
system_config_table = Table(
    "system_config",
    metadata,
    Column("id", Integer, primary_key=True, default=1),
    Column("is_initialized", Boolean, default=False),
    Column("admin_password_hash", String(128)),
    Column("created_at", DateTime, server_default=func.now()),
    Column("app_start_time", DateTime)
)

# 登录失败记录表
login_failed_records_table = Table(
    "login_failed_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ip_address", String(45), nullable=False, comment="IP地址"),
    Column("failed_time", DateTime, nullable=False, server_default=func.now(), comment="失败时间"),
    Column("user_agent", String(500), comment="用户代理"),
    sqlite_autoincrement=True
)

# 密码重置验证码表
password_reset_codes_table = Table(
    "password_reset_codes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("code", String(10), nullable=False, unique=True, comment="验证码"),
    Column("created_at", DateTime, nullable=False, server_default=func.now(), comment="创建时间"),
    Column("expires_at", DateTime, nullable=False, comment="过期时间"),
    Column("is_used", Boolean, default=False, comment="是否已使用"),
    Column("ip_address", String(45), comment="IP地址"),
    sqlite_autoincrement=True
)

__all__ = [
    "system_config_table",
    "login_failed_records_table",
    "password_reset_codes_table"
]
