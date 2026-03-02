# app/modules/acme/models.py
from datetime import datetime

from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from app.core.db.database import engine, metadata

# ========== 1. DNS授权表 ==========
ssl_dns_auth_table = Table(
    "ssl_dns_auth",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 基本信息
    Column("name", String(100), nullable=False),  # 授权名称
    Column("provider", String(50), nullable=False),  # 提供商：tencent/aliyun/cloudflare
    Column("description", String(500)),  # 描述

    # 认证信息（加密存储）
    Column("secret_id", String(500), nullable=False),  # 加密存储
    Column("secret_key", String(500), nullable=False),  # 加密存储

    # 状态
    Column("is_active", Boolean, default=True),
    Column("last_used_at", DateTime),  # 最后使用时间

    # 统计
    Column("total_applications", Integer, default=0),  # 申请次数
    Column("total_success", Integer, default=0),  # 成功次数

    # 时间戳
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),

    sqlite_autoincrement=True,
)


# ========== 2. 证书申请表 ==========
ssl_applications_table = Table(
    "ssl_applications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 关联
    Column("dns_auth_id", Integer, ForeignKey("ssl_dns_auth.id"), nullable=False),

    # 申请信息
    Column("domains", String(1000), nullable=False),  # JSON数组：["example.com", "*.example.com"]
    Column("algorithm", String(20), default="RSA"),  # RSA/ECC
    Column("renew_before", Integer, default=30),  # 到期前多少天自动续期

    # 状态
    Column("status", String(20), default="pending"),  # pending/processing/completed/failed
    Column("last_execution_id", Integer),  # 最后一次执行ID

    # 自动续期配置
    Column("auto_renew", Boolean, default=True),
    Column("next_renew_at", DateTime),  # 下次自动续期时间

    # 备注
    Column("description", String(500)),

    # 时间戳
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),

    sqlite_autoincrement=True,
)


# ========== 3. 申请执行历史表 ==========
ssl_application_executions_table = Table(
    "ssl_application_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 关联
    Column("application_id", Integer, ForeignKey("ssl_applications.id"), nullable=False),

    # 执行信息
    Column("status", String(20), default="pending"),  # pending/processing/success/failed
    Column("triggered_by", String(20), default="system"),  # system/manual

    # 结果
    Column("cert_id", Integer, ForeignKey("ssl_certificates.id")),  # 成功时关联证书
    Column("error", Text),  # 失败时的错误信息
    Column("log", Text),  # 执行日志

    # 执行时间
    Column("started_at", DateTime),
    Column("completed_at", DateTime),

    # 时间戳
    Column("created_at", DateTime, default=datetime.now),

    sqlite_autoincrement=True,
)


# ========== 4. 证书存储表 ==========
ssl_certificates_table = Table(
    "ssl_certificates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 关联
    Column("application_id", Integer, ForeignKey("ssl_applications.id")),  # 来自哪个申请
    Column("execution_id", Integer, ForeignKey("ssl_application_executions.id")),  # 来自哪个执行

    # 证书信息
    Column("domains", String(1000), nullable=False),  # JSON数组
    Column("issuer", String(200)),  # 颁发者
    Column("algorithm", String(20)),  # RSA/ECC

    # 有效期
    Column("not_before", DateTime, nullable=False),
    Column("not_after", DateTime, nullable=False),

    # 文件存储
    Column("cert_path", String(500)),  # 证书文件路径
    Column("key_path", String(500)),  # 私钥文件路径
    Column("fullchain_path", String(500)),  # 完整链文件路径

    # 状态
    Column("is_active", Boolean, default=True),
    Column("renewed_by", Integer, ForeignKey("ssl_certificates.id"), nullable=True),  # 被哪个新证书替换

    # 时间戳
    Column("created_at", DateTime, default=datetime.now),

    sqlite_autoincrement=True,
)


# ========== 5. 证书下载记录表（可选） ==========
ssl_download_logs_table = Table(
    "ssl_download_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    Column("cert_id", Integer, ForeignKey("ssl_certificates.id"), nullable=False),
    Column("downloaded_by", String(100)),  # 下载用户/来源
    Column("downloaded_at", DateTime, default=datetime.now),

    sqlite_autoincrement=True,
)


__all__ = ["ssl_dns_auth_table","ssl_applications_table","ssl_application_executions_table","ssl_certificates_table","ssl_download_logs_table"]
