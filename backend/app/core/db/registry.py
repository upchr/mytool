# app/core/db/registry.py
# from app.modules.note.models import *
# from app.modules.node.models import *
# from app.modules.cron.models import *
# from app.modules.notify.models import *
# from app.modules.sys.models import *
import importlib
import logging
from pathlib import Path
logger = logging.getLogger(__name__)

# 获取 modules 目录的绝对路径
modules_dir = Path.cwd() / "modules"

for item in modules_dir.iterdir():
    if item.is_dir() and (item / "__init__.py").exists():
        modname = item.name
        try:
            importlib.import_module(f'app.modules.{modname}.models')
            logger.info(f"✅ 成功加载模块模型: {modname}")
        except ModuleNotFoundError as e:
            if "models" in str(e):
                logger.debug(f"⏭️ 模块 {modname} 没有 models.py，跳过")
                continue
            else:
                logger.error(f"❌ 加载模块 {modname} 失败: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ 加载模块 {modname} 失败: {e}")
            raise
