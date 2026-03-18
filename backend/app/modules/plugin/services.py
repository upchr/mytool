# app/modules/plugin/services.py
"""
插件模块 - 业务逻辑层

包含：
- PluginService: 插件管理服务
- 插件加载和执行功能
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, update

from app.core.db.utils.query import QueryBuilder
from app.modules.plugin.models import plugins_table, plugin_configs_table
from app.modules.plugin import schemas

logger = logging.getLogger(__name__)


# ========== 插件实例缓存 ==========

_loaded_plugins: Dict[str, Any] = {}  # 已加载的插件实例


class PluginRepository:
    """插件数据访问层"""
    
    def __init__(self, engine):
        self.engine = engine
        self.table = plugins_table
    
    def create(self, data: Dict[str, Any]) -> int:
        """创建插件"""
        query = self.table.insert().values(**data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]
    
    def update(self, plugin_id: str, data: Dict[str, Any]) -> bool:
        """更新插件"""
        query = (
            self.table.update()
            .where(self.table.c.plugin_id == plugin_id)
            .values(**data)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0
    
    def get_by_id(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """根据 plugin_id 获取插件"""
        query = select(self.table).where(self.table.c.plugin_id == plugin_id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取插件列表（分页）"""
        query = QueryBuilder(self.table)
        query.where_eq('is_active', True)
        
        for key, value in filters.items():
            if value is not None:
                if key == 'keyword':
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.table.c, key):
                    query.where_eq(key, value)
        
        return query.paginate(self.engine, page, page_size)


class PluginService:
    """插件管理服务"""
    
    def __init__(self, engine):
        self.repo = PluginRepository(engine)
        self.engine = engine
    
    def create(self, data: schemas.PluginCreate) -> Dict[str, Any]:
        """创建插件"""
        create_data = data.model_dump()
        now = datetime.now()
        create_data.update({
            "created_at": now,
            "updated_at": now
        })
        
        plugin_id = self.repo.create(create_data)
        return self.get_by_id(data.plugin_id)
    
    def update(self, plugin_id: str, data: schemas.PluginUpdate) -> Optional[Dict[str, Any]]:
        """更新插件"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.repo.get_by_id(plugin_id)
        
        update_data["updated_at"] = datetime.now()
        self.repo.update(plugin_id, update_data)
        return self.repo.get_by_id(plugin_id)
    
    def get_by_id(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """获取插件详情"""
        return self.repo.get_by_id(plugin_id)
    
    def get_list(self, params: schemas.PluginQueryParams) -> Dict[str, Any]:
        """获取插件列表"""
        return self.repo.get_list(
            page=params.page,
            page_size=params.page_size,
            plugin_type=params.plugin_type,
            category=params.category,
            is_official=params.is_official,
            is_installed=params.is_installed,
            keyword=params.keyword
        )
    
    def install(self, plugin_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """安装插件"""
        plugin = self.repo.get_by_id(plugin_id)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        # 保存配置
        if config:
            for key, value in config.items():
                self._set_config(plugin_id, key, value)
        
        # 更新安装状态
        self.repo.update(plugin_id, {
            "is_installed": True,
            "updated_at": datetime.now()
        })
        
        return self.repo.get_by_id(plugin_id)
    
    def uninstall(self, plugin_id: str) -> Dict[str, Any]:
        """卸载插件"""
        plugin = self.repo.get_by_id(plugin_id)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        # 卸载已加载的插件实例
        if plugin_id in _loaded_plugins:
            _loaded_plugins[plugin_id].on_unload()
            del _loaded_plugins[plugin_id]
        
        self.repo.update(plugin_id, {
            "is_installed": False,
            "updated_at": datetime.now()
        })
        
        return self.repo.get_by_id(plugin_id)
    
    def load_plugin(self, plugin_id: str) -> Any:
        """
        加载插件实例
        
        Args:
            plugin_id: 插件ID
        
        Returns:
            插件实例
        """
        # 检查缓存
        if plugin_id in _loaded_plugins:
            return _loaded_plugins[plugin_id]
        
        # 获取插件信息
        plugin_info = self.repo.get_by_id(plugin_id)
        if not plugin_info:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        if not plugin_info.get("is_installed"):
            raise ValueError(f"插件未安装: {plugin_id}")
        
        # 获取插件配置
        configs = self.get_configs(plugin_id)
        config = {c["config_key"]: c["config_value"] for c in configs}
        
        # 加载内置插件
        from .plugin_base import get_plugin_by_id
        plugin_class = get_plugin_by_id(plugin_id)
        
        if plugin_class:
            # 实例化插件
            instance = plugin_class(config)
            instance.on_load()
            _loaded_plugins[plugin_id] = instance
            logger.info(f"插件加载成功: {plugin_id}")
            return instance
        
        raise ValueError(f"未知的插件: {plugin_id}")
    
    def send_notification(self, plugin_id: str, title: str, content: str, **kwargs) -> bool:
        """
        发送通知（通知类插件专用）
        
        Args:
            plugin_id: 插件ID
            title: 标题
            content: 内容
            **kwargs: 额外参数
        
        Returns:
            是否发送成功
        """
        from .plugin_base import NotificationPlugin
        
        try:
            instance = self.load_plugin(plugin_id)
            
            if not isinstance(instance, NotificationPlugin):
                raise ValueError(f"插件不是通知类型: {plugin_id}")
            
            return instance.send(title, content, **kwargs)
        except Exception as e:
            logger.error(f"发送通知失败: {plugin_id}, error: {e}")
            return False
    
    def execute_command(self, plugin_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行命令（执行器类插件专用）
        
        Args:
            plugin_id: 插件ID
            command: 要执行的命令
            **kwargs: 额外参数
        
        Returns:
            执行结果
        """
        from .plugin_base import ExecutorPlugin
        
        try:
            instance = self.load_plugin(plugin_id)
            
            if not isinstance(instance, ExecutorPlugin):
                raise ValueError(f"插件不是执行器类型: {plugin_id}")
            
            return instance.execute(command, **kwargs)
        except Exception as e:
            logger.error(f"执行命令失败: {plugin_id}, error: {e}")
            return {"status": "failed", "error": str(e)}
    
    def init_builtin_plugins(self):
        """
        初始化内置插件到数据库
        """
        from .plugin_base import get_builtin_plugins
        
        for plugin_class in get_builtin_plugins():
            plugin_id = plugin_class.plugin_id
            
            # 检查是否已存在
            existing = self.repo.get_by_id(plugin_id)
            if existing:
                continue
            
            # 创建插件记录
            now = datetime.now()
            data = {
                "plugin_id": plugin_id,
                "name": plugin_class.name,
                "version": getattr(plugin_class, "version", "1.0.0"),
                "author": getattr(plugin_class, "author", ""),
                "description": getattr(plugin_class, "description", ""),
                "plugin_type": getattr(plugin_class, "plugin_type", ""),
                "icon": getattr(plugin_class, "icon", "📦"),
                "is_official": True,
                "is_installed": False,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            self.repo.create(data)
            logger.info(f"内置插件初始化: {plugin_id}")
    
    def get_configs(self, plugin_id: str) -> List[Dict[str, Any]]:
        """获取插件配置"""
        query = select(plugin_configs_table).where(
            plugin_configs_table.c.plugin_id == plugin_id
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def _set_config(self, plugin_id: str, key: str, value: str):
        """设置插件配置"""
        now = datetime.now()
        
        # 检查是否存在
        query = select(plugin_configs_table).where(
            plugin_configs_table.c.plugin_id == plugin_id,
            plugin_configs_table.c.config_key == key
        )
        with self.engine.connect() as conn:
            existing = conn.execute(query).first()
        
        if existing:
            update_query = (
                plugin_configs_table.update()
                .where(plugin_configs_table.c.id == existing["id"])
                .values(config_value=value, updated_at=now)
            )
            with self.engine.connect() as conn:
                conn.execute(update_query)
                conn.commit()
        else:
            insert_query = plugin_configs_table.insert().values(
                plugin_id=plugin_id,
                config_key=key,
                config_value=value,
                created_at=now,
                updated_at=now
            )
            with self.engine.connect() as conn:
                conn.execute(insert_query)
                conn.commit()


__all__ = ["PluginService"]
