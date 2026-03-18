# app/modules/plugin/models.py
"""
插件模块 - 数据模型定义

包含：
- plugins_table: 插件定义表
- plugin_configs_table: 插件配置表
"""
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, Boolean, JSON
from app.core.db.database import metadata


# ========== 1. 插件定义表 ==========
plugins_table = Table(
    "plugins",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 基本信息
    Column("plugin_id", String(100), nullable=False, unique=True, comment ="插件唯一标识"),
    Column("name", String(100), nullable=False, comment ="插件名称"),
    Column("version", String(20), default="1.0.0", comment ="版本号"),
    Column("author", String(100), default="MyTool Team", comment ="作者"),
    Column("description", Text, comment ="插件描述"),

    # 分类
    Column("plugin_type", String(50), comment ="插件类型：notification/executor/datasource"),
    Column("category", String(50), comment ="分类"),
    Column("icon", String(10), comment ="图标"),
    Column("tags", JSON, default=list, comment ="标签列表"),

    # 入口
    Column("entry_point", String(200), comment ="入口点：module_path:ClassName"),
    Column("permissions", JSON, default=list, comment ="需要的权限列表"),

    # 状态
    Column("is_official", Boolean, default=True, comment ="是否官方插件"),
    Column("is_installed", Boolean, default=False, comment ="是否已安装"),
    Column("is_active", Boolean, default=True, comment ="是否启用"),

    # 统计
    Column("download_count", Integer, default=0, comment ="下载次数"),
    Column("rating_count", Integer, default=0, comment ="评分次数"),
    Column("rating_avg", Integer, default=0, comment ="平均评分"),

    # 时间戳
    Column("created_at", DateTime, default=datetime.now, comment ="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment ="更新时间"),

    sqlite_autoincrement=True,
)


# ========== 2. 插件配置表 ==========
plugin_configs_table = Table(
    "plugin_configs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 关联
    Column("plugin_id", String(100), nullable=False, comment ="插件ID"),

    # 配置
    Column("config_key", String(100), nullable=False, comment ="配置键"),
    Column("config_value", Text, comment ="配置值"),
    Column("config_type", String(20), default="string", comment ="配置类型"),
    Column("is_secret", Boolean, default=False, comment ="是否敏感信息"),

    # 时间戳
    Column("created_at", DateTime, default=datetime.now, comment ="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment ="更新时间"),

    sqlite_autoincrement=True,
)


__all__ = ["plugins_table", "plugin_configs_table"]
