# app/core/db/init_db.py
import logging
from app.core.db.database import metadata,engine
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

def upgrade():
    logger.debug("🔧 检测数据库字段升级...")

    from .db_upgrade import VersionedAutoMigrator

    migrator = VersionedAutoMigrator(engine, metadata)
    results = migrator.sync_all()

    if results:
        for table, fields in results.items():
            logger.info(f"表 {table} 自动添加了字段: {', '.join(fields)}")
    else:
        logger.info("✅ 所有表已是最新")
    logger.debug("✅ 检测数据库字段升级完成！")


def init_database():
    create_all_tables()
    init_module_data()
    upgrade()
