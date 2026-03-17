from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from app.core.db.database import engine, metadata
from datetime import datetime

# 任务模板表
task_templates_table = Table(
    "task_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_id", String(100), nullable=False, unique=True),  # 模板唯一标识
    Column("name", String(100), nullable=False),  # 模板名称
    Column("version", String(20), nullable=False, default="1.0.0"),  # 模板版本
    Column("author", String(100), nullable=False, default="MyTool Team"),  # 作者
    Column("description", Text),  # 模板描述
    Column("category", String(50), nullable=False),  # 分类：系统运维类/开发工具类/个人助理类/网络监控类
    Column("tags", JSON, default=list),  # 标签数组
    Column("difficulty", String(20), nullable=False, default="入门"),  # 难度：入门/中级/高级
    Column("icon", String(50)),  # 图标emoji
    Column("is_official", Boolean, default=True),  # 是否官方模板
    Column("is_enabled", Boolean, default=True),  # 是否启用
    Column("download_count", Integer, default=0),  # 下载次数
    Column("rating_count", Integer, default=0),  # 评分次数
    Column("rating_avg", Integer, default=0),  # 平均评分（0-5）
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 模板配置Schema表
template_schemas_table = Table(
    "template_schemas",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_id", String(100), ForeignKey("task_templates.template_id"), nullable=False),
    Column("schema_json", JSON, nullable=False),  # 参数配置Schema（JSON格式）
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 模板脚本表
template_scripts_table = Table(
    "template_scripts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_id", String(100), ForeignKey("task_templates.template_id"), nullable=False),
    Column("script_type", String(20), nullable=False, default="python"),  # 脚本类型：python/shell
    Column("script_content", Text, nullable=False),  # 脚本内容
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

# 模板Cron建议表
template_cron_suggestions_table = Table(
    "template_cron_suggestions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_id", String(100), ForeignKey("task_templates.template_id"), nullable=False),
    Column("label", String(100), nullable=False),  # 建议标签，如"每天早上8点"
    Column("cron_value", String(50), nullable=False),  # Cron表达式
    Column("is_default", Boolean, default=False),  # 是否默认
    Column("sort_order", Integer, default=0),  # 排序
    sqlite_autoincrement=True,
)

# 模板用户评分表
template_ratings_table = Table(
    "template_ratings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_id", String(100), ForeignKey("task_templates.template_id"), nullable=False),
    Column("user_id", Integer, nullable=False),  # 用户ID
    Column("rating", Integer, nullable=False),  # 评分1-5
    Column("comment", Text),  # 评论
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    sqlite_autoincrement=True,
)

__all__ = [
    "task_templates_table",
    "template_schemas_table",
    "template_scripts_table",
    "template_cron_suggestions_table",
    "template_ratings_table"
]
