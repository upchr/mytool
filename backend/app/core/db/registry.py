# app/core/db/registry.py

# from app.modules.note.models import *
# from app.modules.node.models import *
# from app.modules.cron.models import *
# from app.modules.notify.models import *
# from app.modules.sys.models import *
import pkgutil
import importlib
import logging

logger = logging.getLogger(__name__)

for importer, modname, ispkg in pkgutil.iter_modules(['app/modules']):
    if ispkg:
        try:
            importlib.import_module(f'app.modules.{modname}.models')
            logger.info(f"✅ 成功加载模块模型: {modname}")
        except ModuleNotFoundError as e:
            # 如果模块没有 models.py，跳过（正常情况）
            if "models" in str(e):
                logger.debug(f"⏭️ 模块 {modname} 没有 models.py，跳过")
                continue
            else:
                # 其他导入错误，重新抛出
                logger.error(f"❌ 加载模块 {modname} 失败: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ 加载模块 {modname} 失败: {e}")
            raise
