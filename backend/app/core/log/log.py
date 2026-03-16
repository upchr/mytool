import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

LEVEL_ICONS = {
    logging.DEBUG: "🐛",
    logging.INFO: "ℹ️ ",
    logging.WARNING: "⚠️ ",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥",
}

class IconFormatter(logging.Formatter):
    def format(self, record):
        record.asctime = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        record.levelicon = LEVEL_ICONS.get(record.levelno, "")
        return f"{record.asctime} {record.levelicon}[{record.name}] {record.getMessage()}"

class PlainFormatter(logging.Formatter):
    def __init__(self, fmt=None):
        super().__init__(fmt or "%(asctime)s %(levelname)-8s [%(name)s] %(funcName)s:%(lineno)d - %(message)s")

def setup_logging(config_obj):
    # 配置根日志器（root logger）
    root_logger = logging.getLogger()
    print(f"默认日志级别：{config_obj.LOG_LEVEL}")

    root_logger.setLevel(config_obj.LOG_LEVEL)

    # 清除已有 handler（避免重复）
    if root_logger.handlers:
        root_logger.handlers.clear()

    env = getattr(config_obj, 'ENVIRONMENT', 'dev')

    if env == 'prod':
        # 生产环境：写入文件
        os.makedirs(config_obj.LOG_DIR, exist_ok=True)
        log_path = os.path.join(config_obj.LOG_DIR, config_obj.LOG_FILENAME)
        handler = RotatingFileHandler(
            log_path,
            maxBytes=config_obj.LOG_MAX_BYTES,
            backupCount=config_obj.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(PlainFormatter(config_obj.LOG_FORMAT_FILE))
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    else:
        # 开发环境：根据控制台编码选择是否使用表情
        handler = logging.StreamHandler(sys.stdout)
        encoding = getattr(sys.stdout, "encoding", "") or ""
        if encoding.lower().startswith("utf"):
            handler.setFormatter(IconFormatter())
        else:
            # 避免 Windows GBK 控制台输出 emoji 导致 UnicodeEncodeError
            handler.setFormatter(PlainFormatter())

        logging.getLogger("sqlalchemy.engine").setLevel(config_obj.LOG_LEVEL)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    root_logger.addHandler(handler)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
