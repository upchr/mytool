# app/core/routers.py
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


class RouterManager:
    """路由管理器"""

    def __init__(self):
        self.routers = []
        self._discover_routers()

    def _discover_routers(self):
        """自动发现所有模块的路由"""
        import pkgutil
        import importlib
        from pathlib import Path

        modules_path = Path.cwd() / 'modules'

        for item in modules_path.iterdir():
            if item.is_dir() and (item / "api.py").exists():
                modname = item.name
                try:
                    # 尝试导入模块的 api
                    module = importlib.import_module(f'app.modules.{modname}.api')

                    # 查找 router 变量
                    if hasattr(module, 'router'):
                        router = getattr(module, 'router')
                        self.routers.append({
                            'name': modname,
                            'router': router,
                            'prefix': getattr(router, 'prefix', '')
                        })
                        logger.info(f"✅ 发现路由: {modname}")

                except ModuleNotFoundError:
                    # 没有 api.py 是正常的
                    pass
                except Exception as e:
                    logger.error(f"❌ 加载模块 {modname} 路由失败: {e}")

    def register_routers(self, app: FastAPI):
        """注册所有路由到应用"""
        for router_info in self.routers:
            app.include_router(router_info['router'])
            logger.info(f"📌 已注册路由: {router_info['name']} (前缀: {router_info['prefix']})")

        logger.info(f"✅ 共注册 {len(self.routers)} 个路由模块")


# 全局实例
router_manager = RouterManager()
