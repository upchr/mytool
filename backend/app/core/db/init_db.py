# app/core/db/init_db.py
import logging

from app.core.db.database import engine, metadata
from app.core.db.registry import *  # 触发所有表注册
logger = logging.getLogger(__name__)

def create_all_tables():
    logger.debug("🔧 创建数据库表...")
    metadata.create_all(bind=engine)
    logger.debug("✅ 表创建完成！")

def init_module_data():
    logger.debug("🔧 初始化业务数据...")
    from app.modules.notify.models import init_default_notification_services
    init_default_notification_services()
    logger.debug("✅ 初始化业务数据完成！")

def init_database():
    create_all_tables()
    init_module_data()
