from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func
from app.core.db.database import database
from .models import (
    plugins_table,
    plugin_configs_table,
    plugin_ratings_table,
    plugin_logs_table
)
from .schemas import (
    PluginCreate,
    PluginUpdate,
    PluginConfigCreate,
    PluginRatingCreate,
    PluginQueryParams
)
from .plugin_base import BasePlugin, PluginSandbox
from .builtin_plugins import get_builtin_plugins
import importlib
import logging
import os

logger = logging.getLogger(__name__)


class PluginService:
    """插件服务"""

    # 已加载的插件缓存
    _loaded_plugins: Dict[str, BasePlugin] = {}
    # 插件沙箱缓存
    _plugin_sandboxes: Dict[str, PluginSandbox] = {}
    # 插件热重载监控
    _plugin_mtimes: Dict[str, float] = {}

    @staticmethod
    async def get_plugin(plugin_id: str) -> Optional[Dict]:
        """获取单个插件"""
        query = select(plugins_table).where(plugins_table.c.plugin_id == plugin_id)
        return await database.fetch_one(query)

    @staticmethod
    async def list_plugins(params: PluginQueryParams) -> tuple[List[Dict], int]:
        """列出插件（带分页和筛选）"""
        query = select(plugins_table).where(plugins_table.c.is_enabled == True)

        # 筛选条件
        if params.plugin_type:
            query = query.where(plugins_table.c.plugin_type == params.plugin_type)
        if params.category:
            query = query.where(plugins_table.c.category == params.category)
        if params.is_official is not None:
            query = query.where(plugins_table.c.is_official == params.is_official)
        if params.is_installed is not None:
            query = query.where(plugins_table.c.is_installed == params.is_installed)
        if params.keyword:
            keyword = f"%{params.keyword}%"
            query = query.where(
                or_(
                    plugins_table.c.name.like(keyword),
                    plugins_table.c.description.like(keyword)
                )
            )

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await database.fetch_val(count_query)

        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.order_by(plugins_table.c.download_count.desc()).offset(offset).limit(params.page_size)

        plugins = await database.fetch_all(query)
        return plugins, total

    @staticmethod
    async def create_plugin(data: PluginCreate) -> Dict:
        """创建插件"""
        now = datetime.utcnow()
        query = plugins_table.insert().values(
            **data.model_dump(),
            created_at=now,
            updated_at=now
        )
        record_id = await database.execute(query)

        return await PluginService.get_plugin(data.plugin_id)

    @staticmethod
    async def update_plugin(plugin_id: str, data: PluginUpdate) -> Optional[Dict]:
        """更新插件"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await PluginService.get_plugin(plugin_id)

        update_data["updated_at"] = datetime.utcnow()
        query = (
            update(plugins_table)
            .where(plugins_table.c.plugin_id == plugin_id)
            .values(**update_data)
        )
        await database.execute(query)
        return await PluginService.get_plugin(plugin_id)

    @staticmethod
    async def delete_plugin(plugin_id: str) -> bool:
        """删除插件"""
        query = (
            update(plugins_table)
            .where(plugins_table.c.plugin_id == plugin_id)
            .values(is_enabled=False, updated_at=datetime.utcnow())
        )
        await database.execute(query)
        return True

    @staticmethod
    async def install_plugin(plugin_id: str, config: Optional[Dict[str, Any]] = None) -> Dict:
        """安装插件"""
        plugin = await PluginService.get_plugin(plugin_id)
        if not plugin:
            raise ValueError("插件不存在")

        # 更新插件状态
        query = (
            update(plugins_table)
            .where(plugins_table.c.plugin_id == plugin_id)
            .values(
                is_installed=True,
                installed_at=datetime.utcnow(),
                download_count=plugins_table.c.download_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        await database.execute(query)

        # 保存配置
        if config:
            for key, value in config.items():
                await PluginService.set_config(plugin_id, key, str(value))

        # 加载插件
        await PluginService.load_plugin(plugin_id)

        return await PluginService.get_plugin(plugin_id)

    @staticmethod
    async def uninstall_plugin(plugin_id: str) -> Dict:
        """卸载插件"""
        # 先卸载
        if plugin_id in PluginService._loaded_plugins:
            try:
                PluginService._loaded_plugins[plugin_id].on_unload()
            except Exception as e:
                logger.error(f"插件卸载时出错: {e}")
            del PluginService._loaded_plugins[plugin_id]

        # 更新状态
        query = (
            update(plugins_table)
            .where(plugins_table.c.plugin_id == plugin_id)
            .values(
                is_installed=False,
                installed_at=None,
                updated_at=datetime.utcnow()
            )
        )
        await database.execute(query)

        return await PluginService.get_plugin(plugin_id)

    @staticmethod
    async def load_plugin(plugin_id: str, force_reload: bool = False) -> Optional[BasePlugin]:
        """加载插件（支持热重载）"""
        plugin = await PluginService.get_plugin(plugin_id)
        if not plugin:
            return None

        # 检查是否已加载且不需要强制重载
        if not force_reload and plugin_id in PluginService._loaded_plugins:
            # 检查是否需要热重载
            if await PluginService._check_plugin_changed(plugin_id):
                logger.info(f"插件文件变化，触发热重载: {plugin_id}")
                await PluginService.unload_plugin(plugin_id)
            else:
                return PluginService._loaded_plugins[plugin_id]

        try:
            # 先查找内置插件
            builtin_plugins = {p.plugin_id: p for p in get_builtin_plugins()}
            if plugin_id in builtin_plugins:
                PluginClass = builtin_plugins[plugin_id]
            else:
                # 动态加载外部插件
                entry_point = plugin["entry_point"]
                module_name, class_name = entry_point.split(":")
                
                # 热重载：重新加载模块
                if module_name in importlib.sys.modules and force_reload:
                    importlib.reload(importlib.sys.modules[module_name])
                
                module = importlib.import_module(module_name)
                PluginClass = getattr(module, class_name)

            # 获取插件配置
            configs = await PluginService.get_configs(plugin_id)
            config = {c["config_key"]: c["config_value"] for c in configs}

            # 获取插件声明的权限和数据库中配置的权限
            declared_perms = getattr(PluginClass, "required_permissions", [])
            plugin_perms = plugin.get("permissions", [])
            granted_perms = set(declared_perms) & set(plugin_perms)

            # 创建插件沙箱
            plugin_data_dir = f"/data/plugins/{plugin_id}"
            os.makedirs(plugin_data_dir, exist_ok=True)
            sandbox = PluginSandbox(plugin_id, allowed_dirs=[plugin_data_dir])
            PluginService._plugin_sandboxes[plugin_id] = sandbox

            # 实例化插件
            plugin_instance = PluginClass(config, granted_permissions=granted_perms)
            plugin_instance.set_logger(logger)
            plugin_instance._sandbox_context = {"sandbox": sandbox, "data_dir": plugin_data_dir}

            # 调用on_load
            plugin_instance.on_load()

            # 缓存
            PluginService._loaded_plugins[plugin_id] = plugin_instance
            
            # 记录文件修改时间用于热重载
            await PluginService._record_plugin_mtime(plugin_id, plugin)

            await PluginService._log(plugin_id, "load", "插件加载成功", metadata={"permissions": list(granted_perms)})
            logger.info(f"插件加载成功: {plugin_id}, permissions={list(granted_perms)}")
            return plugin_instance

        except Exception as e:
            logger.error(f"插件加载失败: {plugin_id}, error: {e}")
            await PluginService._log(plugin_id, "error", f"插件加载失败: {e}", "error")
            return None
    
    @staticmethod
    async def unload_plugin(plugin_id: str):
        """卸载插件"""
        if plugin_id in PluginService._loaded_plugins:
            try:
                PluginService._loaded_plugins[plugin_id].on_unload()
            except Exception as e:
                logger.error(f"插件卸载时出错: {plugin_id}, error: {e}")
            del PluginService._loaded_plugins[plugin_id]
        
        if plugin_id in PluginService._plugin_sandboxes:
            del PluginService._plugin_sandboxes[plugin_id]
        
        if plugin_id in PluginService._plugin_mtimes:
            del PluginService._plugin_mtimes[plugin_id]
    
    @staticmethod
    async def _check_plugin_changed(plugin_id: str) -> bool:
        """检查插件文件是否变化（用于热重载）"""
        if plugin_id not in PluginService._plugin_mtimes:
            return False
        
        plugin = await PluginService.get_plugin(plugin_id)
        if not plugin or plugin.get("is_official", True):
            return False
        
        entry_point = plugin.get("entry_point", "")
        if ":" not in entry_point:
            return False
        
        module_name = entry_point.split(":")[0]
        if module_name not in importlib.sys.modules:
            return False
        
        module = importlib.sys.modules[module_name]
        if not hasattr(module, "__file__") or not module.__file__:
            return False
        
        try:
            current_mtime = os.path.getmtime(module.__file__)
            return current_mtime > PluginService._plugin_mtimes.get(plugin_id, 0)
        except Exception:
            return False
    
    @staticmethod
    async def _record_plugin_mtime(plugin_id: str, plugin: Dict):
        """记录插件文件修改时间"""
        if plugin.get("is_official", True):
            return
        
        entry_point = plugin.get("entry_point", "")
        if ":" not in entry_point:
            return
        
        module_name = entry_point.split(":")[0]
        if module_name not in importlib.sys.modules:
            return
        
        module = importlib.sys.modules[module_name]
        if not hasattr(module, "__file__") or not module.__file__:
            return
        
        try:
            PluginService._plugin_mtimes[plugin_id] = os.path.getmtime(module.__file__)
        except Exception:
            pass

    @staticmethod
    def get_loaded_plugin(plugin_id: str) -> Optional[BasePlugin]:
        """获取已加载的插件"""
        return PluginService._loaded_plugins.get(plugin_id)

    @staticmethod
    async def call_plugin(plugin_id: str, method: str, params: Dict[str, Any]) -> Any:
        """调用插件方法"""
        plugin_instance = PluginService.get_loaded_plugin(plugin_id)
        if not plugin_instance:
            plugin_instance = await PluginService.load_plugin(plugin_id)
            if not plugin_instance:
                raise ValueError(f"插件未找到或加载失败: {plugin_id}")

        try:
            func = getattr(plugin_instance, method)
            result = func(**params)
            await PluginService._log(plugin_id, "call", f"调用方法 {method} 成功")
            return result
        except Exception as e:
            await PluginService._log(plugin_id, "error", f"调用方法 {method} 失败: {e}", "error")
            raise

    # ========== 配置相关 ==========

    @staticmethod
    async def get_configs(plugin_id: str) -> List[Dict]:
        """获取插件的所有配置"""
        query = select(plugin_configs_table).where(plugin_configs_table.c.plugin_id == plugin_id)
        return await database.fetch_all(query)

    @staticmethod
    async def set_config(plugin_id: str, key: str, value: str, config_type: str = "string", is_secret: bool = False):
        """设置插件配置"""
        # 检查是否已存在
        existing_query = select(plugin_configs_table).where(
            and_(
                plugin_configs_table.c.plugin_id == plugin_id,
                plugin_configs_table.c.config_key == key
            )
        )
        existing = await database.fetch_one(existing_query)

        now = datetime.utcnow()
        if existing:
            query = (
                update(plugin_configs_table)
                .where(plugin_configs_table.c.id == existing["id"])
                .values(
                    config_value=value,
                    config_type=config_type,
                    is_secret=is_secret,
                    updated_at=now
                )
            )
        else:
            query = plugin_configs_table.insert().values(
                plugin_id=plugin_id,
                config_key=key,
                config_value=value,
                config_type=config_type,
                is_secret=is_secret,
                created_at=now,
                updated_at=now
            )
        await database.execute(query)

    # ========== 评分相关 ==========

    @staticmethod
    async def create_rating(data: PluginRatingCreate) -> Dict:
        """创建评分"""
        query = plugin_ratings_table.insert().values(**data.model_dump())
        record_id = await database.execute(query)

        # 更新插件的平均评分
        await PluginService._update_plugin_rating(data.plugin_id)

        get_query = select(plugin_ratings_table).where(plugin_ratings_table.c.id == record_id)
        return await database.fetch_one(get_query)

    @staticmethod
    async def _update_plugin_rating(plugin_id: str):
        """更新插件的平均评分"""
        query = select(
            func.count(plugin_ratings_table.c.id).label("count"),
            func.avg(plugin_ratings_table.c.rating).label("avg")
        ).where(plugin_ratings_table.c.plugin_id == plugin_id)
        result = await database.fetch_one(query)

        if result and result["count"] > 0:
            update_query = (
                update(plugins_table)
                .where(plugins_table.c.plugin_id == plugin_id)
                .values(
                    rating_count=result["count"],
                    rating_avg=int(result["avg"]),
                    updated_at=datetime.utcnow()
                )
            )
            await database.execute(update_query)

    # ========== 日志相关 ==========

    @staticmethod
    async def _log(plugin_id: str, action: str, message: str, level: str = "info", metadata: Optional[Dict] = None):
        """记录插件日志"""
        query = plugin_logs_table.insert().values(
            plugin_id=plugin_id,
            action=action,
            message=message,
            level=level,
            metadata=metadata or {}
        )
        await database.execute(query)


# ========== 初始化内置插件 ==========

async def init_builtin_plugins():
    """初始化内置插件到数据库"""
    from .schemas import PluginCreate

    for PluginClass in get_builtin_plugins():
        # 检查是否已存在
        existing = await PluginService.get_plugin(PluginClass.plugin_id)
        if existing:
            continue

        # 创建插件
        plugin_data = PluginCreate(
            plugin_id=PluginClass.plugin_id,
            name=PluginClass.name,
            version=PluginClass.version,
            author=PluginClass.author,
            description=PluginClass.description,
            plugin_type=PluginClass.plugin_type,
            category=PluginClass.category,
            entry_point="",  # 内置插件不需要
            permissions=[],
            icon=PluginClass.icon,
            is_official=True,
            is_enabled=True
        )
        await PluginService.create_plugin(plugin_data)
        logger.info(f"内置插件初始化完成: {PluginClass.plugin_id}")
