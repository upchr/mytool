# notify/__init__.py
import importlib
import logging
import os
from typing import Dict, Type
from .base import NotificationStrategy

logger = logging.getLogger(__name__)

class NotificationStrategyFactory:

    _strategies: Dict[str, Type[NotificationStrategy]] = {}
    _initialized = False
    _use_registry = True  # 是否使用注册表模式

    @classmethod
    def _lazy_init(cls):
        if not cls._initialized:
            cls._init_strategies()

    @classmethod
    def _init_strategies(cls):
        """初始化策略"""
        if cls._initialized:
            return

        if cls._use_registry:
            cls._init_via_registry()
        else:
            cls._init_via_discovery()

        cls._initialized = True
        logger.info(f"策略初始化完成，找到 {len(cls._strategies)} 个策略: {list(cls._strategies.keys())}")

    @classmethod
    def _init_via_registry(cls):
        """通过注册表初始化"""
        try:
            # 导入注册表模块，这会触发所有策略模块的导入
            from . import registry
            logger.info("✓ 使用注册表模式初始化策略")

            # 从注册表模块中提取策略类
            import sys
            registry_module = sys.modules['app.modules.notify.handler.registry']

            for attr_name in dir(registry_module):
                attr = getattr(registry_module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, NotificationStrategy) and
                        attr != NotificationStrategy):

                    name = attr.get_strategy_name()
                    if name:
                        cls._strategies[name] = attr
                        logger.info(f"✓ 注册策略: {name} (来自 registry)")

        except ImportError as e:
            logger.debug(f"✗ 注册表导入失败: {e}")
            # 回退到动态发现
            cls._init_via_discovery()

    @classmethod
    def _init_via_discovery(cls):
        """通过动态发现初始化"""
        package = __package__
        if not package:
            return

        package_dir = os.path.dirname(__file__)

        # 扫描目录中的 .py 文件
        for filename in os.listdir(package_dir):
            if filename.endswith('.py') and filename not in ['__init__.py', 'base.py', 'manager.py', 'registry.py']:
                module_name = filename[:-3]  # 去掉 .py
                full_module_name = f"{package}.{module_name}"
                cls._load_strategy_module(full_module_name)

    @classmethod
    def _load_strategy_module(cls, module_name: str):
        """加载策略模块"""
        try:
            module = importlib.import_module(module_name)

            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                            issubclass(attr, NotificationStrategy) and
                            attr != NotificationStrategy):

                        name = attr.get_strategy_name()
                        if name and name not in cls._strategies:
                            cls._strategies[name] = attr
                            logger.info(f"✓ 注册策略: {name} (来自 {module_name})")

                except Exception:
                    pass

        except Exception as e:
            logger.debug(f"✗ 加载模块 {module_name} 失败: {e}")

    @classmethod
    def get_strategy(cls, strategy_type: str, config: Dict) -> NotificationStrategy:
        """获取策略实例"""
        cls._lazy_init()  # 懒加载初始化

        strategy_type = strategy_type.lower()
        strategy_class = cls._strategies.get(strategy_type)

        if not strategy_class:
            available = list(cls._strategies.keys())
            raise ValueError(f"不支持的通知策略: {strategy_type}。可用策略: {available}")

        return strategy_class(config)

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[NotificationStrategy]):
        """手动注册策略"""
        cls._strategies[name.lower()] = strategy_class

    @classmethod
    def get_available_strategies(cls) -> Dict[str, Type[NotificationStrategy]]:
        """获取所有可用策略"""
        cls._lazy_init()  # 懒加载初始化
        return cls._strategies.copy()

    @classmethod
    def get_strategy_names(cls) -> list:
        """获取策略名称列表"""
        cls._lazy_init()  # 懒加载初始化
        return list(cls._strategies.keys())

    @classmethod
    def clear_strategies(cls):
        """清空策略（用于测试）"""
        cls._strategies.clear()
        cls._initialized = False
        logger.info("已清空策略缓存")

    @classmethod
    def use_registry_mode(cls, enable: bool = True):
        """设置是否使用注册表模式"""
        cls._use_registry = enable
        cls._initialized = False  # 重置状态，下次调用会重新初始化
        logger.info(f"已设置注册表模式: {enable}")

    @classmethod
    def preload(cls):
        """预加载策略（主动调用）"""
        cls._lazy_init()
        return cls._strategies.copy()
