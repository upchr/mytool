# app/modules/task_template/models.py
"""
任务模板模块 - 数据模型定义

包含：
- task_templates_table: 任务模板表
- template_categories_table: 模板分类表
"""
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, Boolean, JSON
from app.core.db.database import metadata


# ========== 1. 任务模板表 ==========
task_templates_table = Table(
    "task_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    
    # 基本信息
    Column("template_id", String(100), nullable=False, unique=True, description="模板唯一标识"),
    Column("name", String(100), nullable=False, description="模板名称"),
    Column("description", Text, description="模板描述"),
    
    # 分类
    Column("category", String(50), description="分类"),
    Column("tags", JSON, default=list, description="标签列表"),
    Column("icon", String(10), default="📝", description="图标"),
    
    # 脚本内容
    Column("script_type", String(20), default="shell", description="脚本类型：shell/python"),
    Column("script_content", Text, description="脚本内容"),
    Column("config_schema", JSON, description="配置项 Schema"),
    
    # Cron 建议
    Column("default_cron", String(50), description="默认 Cron 表达式"),
    Column("cron_description", String(200), description="Cron 说明"),
    
    # 统计
    Column("download_count", Integer, default=0, description="下载次数"),
    Column("rating_count", Integer, default=0, description="评分次数"),
    Column("rating_avg", Integer, default=0, description="平均评分"),
    
    # 状态
    Column("is_official", Boolean, default=True, description="是否官方模板"),
    Column("is_active", Boolean, default=True, description="是否启用"),
    
    # 时间戳
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, description="更新时间"),
    
    sqlite_autoincrement=True,
)


__all__ = ["task_templates_table"]
