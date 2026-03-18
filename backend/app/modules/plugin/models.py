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
    Column("plugin_id", String(100), nullable=False, unique=True, description="插件唯一标识"),
    Column("name", String(100), nullable=False, description="插件名称"),
    Column("version", String(20), default="1.0.0", description="版本号"),
    Column("author", String(100), default="MyTool Team", description="作者"),
    Column("description", Text, description="插件描述"),
    
    # 分类
    Column("plugin_type", String(50), description="插件类型：notification/executor/datasource"),
    Column("category", String(50), description="分类"),
    Column("icon", String(10), description="图标"),
    Column("tags", JSON, default=list, description="标签列表"),
    
    # 入口
    Column("entry_point", String(200), description="入口点：module_path:ClassName"),
    Column("permissions", JSON, default=list, description="需要的权限列表"),
    
    # 状态
    Column("is_official", Boolean, default=True, description="是否官方插件"),
    Column("is_installed", Boolean, default=False, description="是否已安装"),
    Column("is_active", Boolean, default=True, description="是否启用"),
    
    # 统计
    Column("download_count", Integer, default=0, description="下载次数"),
    Column("rating_count", Integer, default=0, description="评分次数"),
    Column("rating_avg", Integer, default=0, description="平均评分"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, description="更新时间"),
    
    sqlite_autoincrement=True,
)


# ========== 2. 插件配置表 ==========
plugin_configs_table = Table(
    "plugin_configs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 关联
    Column("plugin_id", String(100), nullable=False, description="插件ID"),
    
    # 配置
    Column("config_key", String(100), nullable=False, description="配置键"),
    Column("config_value", Text, description="配置值"),
    Column("config_type", String(20), default="string", description="配置类型"),
    Column("is_secret", Boolean, default=False, description="是否敏感信息"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, description="更新时间"),
    
    sqlite_autoincrement=True,
)


__all__ = ["plugins_table", "plugin_configs_table"]
