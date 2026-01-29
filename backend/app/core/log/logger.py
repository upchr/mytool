import logging
import sys
from datetime import datetime

LEVEL_ICONS = {
    logging.DEBUG: "🐛",
    logging.INFO: "ℹ️ ",
    logging.WARNING: "⚠️ ",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥",
}
"""日志管理"""
class IconFormatter(logging.Formatter):
    def format(self, record):
        record.asctime = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        record.levelicon = LEVEL_ICONS.get(record.levelno, "")
        return super().format(record)

def setup_logger(level=logging.INFO):
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    _LOGGER = logging.getLogger("DeviceControl")
    _LOGGER.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = IconFormatter(fmt="%(asctime)s %(levelicon)s[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.propagate = False  # 避免重复输出

    return _LOGGER

_LOGGER = None
