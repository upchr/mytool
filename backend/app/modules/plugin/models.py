from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from app.core.db.database import engine, metadata
from datetime import datetime

# 插件表
plugins_table = Table(
    "plugins",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plugin_id", String(100), nullable=False, unique=True),  # 插件唯一标识
    Column("name", String(100), nullable=False),  # 插件名称
    Column("version", String(20), nullable=False, default="1.0.0"),  # 插件版本
    Column("author", String(100), nullable=False, default="MyTool Team"),  # 作者
    Column("description", Text),  # 插件描述
    Column("plugin_type", String(50), nullable=False),  # 插件类型：notification/executor/datasource/trigger/storage/ai
    Column("category", String(50)),  # 分类
    Column("entry_point", String(200), nullable=False),  # 入口点，如 "myplugin.plugin:MyPlugin"
    Column("permissions", JSON, default=list),  # 权限列表
    Column("icon", String(50)),  # 图标emoji
    Column("homepage", String(255)),  # 主页链接
    Column("repository", String(255)),  # 仓库链接
    Column("license", String(50)),  # 许可证
    Column("is_official", Boolean, default=False),  # 是否官方插件
    Column("is_enabled", Boolean, default=True),  # 是否启用
    Column("is_installed", Boolean, default=False),  # 是否安装
    Column("download_count", Integer, default=0),  # 下载次数
    Column("rating_count", Integer, default=0),  # 评分次数
    Column("rating_avg", Integer, default=0),  # 平均评分（0-5）
    Column("installed_at", DateTime),  # 安装时间
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 插件配置表
plugin_configs_table = Table(
    "plugin_configs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plugin_id", String(100), ForeignKey("plugins.plugin_id"), nullable=False),
    Column("config_key", String(100), nullable=False),  # 配置键
    Column("config_value", Text),  # 配置值
    Column("config_type", String(20), default="string"),  # 配置类型：string/number/boolean/json
    Column("is_secret", Boolean, default=False),  # 是否加密存储
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 插件评分表
plugin_ratings_table = Table(
    "plugin_ratings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plugin_id", String(100), ForeignKey("plugins.plugin_id"), nullable=False),
    Column("user_id", Integer, nullable=False),  # 用户ID
    Column("rating", Integer, nullable=False),  # 评分1-5
    Column("comment", Text),  # 评论
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 插件执行日志表
plugin_logs_table = Table(
    "plugin_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plugin_id", String(100), ForeignKey("plugins.plugin_id"), nullable=False),
    Column("action", String(50), nullable=False),  # 操作：load/unload/call/error
    Column("message", Text),  # 日志消息
    Column("level", String(20), default="info"),  # 日志级别：info/warning/error
    Column("metadata", JSON, default=dict),  # 元数据
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

__all__ = [
    "plugins_table",
    "plugin_configs_table",
    "plugin_ratings_table",
    "plugin_logs_table"
]
