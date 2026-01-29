# config/__init__.py
import os
import logging
import sys
from pathlib import Path

class Config:
    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.INFO
    LOG_FORMAT_CONSOLE = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    LOG_FORMAT_FILE = "%(asctime)s %(levelname)-8s [%(name)s] %(funcName)s:%(lineno)d - %(message)s"
    if sys.platform.startswith("win"):
        LOG_DIR = Path.cwd().parent.parent / "data/logs"
    else:
        LOG_DIR=Path("/toolsplus/data/logs")
    LOG_FILENAME = "app.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10

class DevelopmentConfig(Config):
    DEBUG = True
    ENVIRONMENT = "dev"
    LOG_LEVEL = logging.DEBUG

class ProductionConfig(Config):
    DEBUG = False
    ENVIRONMENT = "prod"
    LOG_LEVEL = logging.INFO

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENVIRONMENT = "test"
    LOG_LEVEL = logging.WARNING

config = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    if config_name is None:
        config_name = os.getenv('OS_ENV', 'dev')
        print(f"启动环境：{config_name}")
    return config.get(config_name, config['default'])
