"""
CPE 模块

烽火 5G CPE 路由器管理
"""

from .api import router
from .models import cpe_config_table, cpe_sms_table
from . import schemas, services

__all__ = ["router", "cpe_config_table", "cpe_sms_table", "schemas", "services"]
