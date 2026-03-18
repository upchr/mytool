# app/modules/plugin/services.py
"""
插件模块 - 业务逻辑层
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, update

from app.core.db.utils.query import QueryBuilder
from app.modules.plugin.models import plugins_table, plugin_configs_table
from app.modules.plugin import schemas

logger = logging.getLogger(__name__)


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
        
        self.repo.update(plugin_id, {
            "is_installed": False,
            "updated_at": datetime.now()
        })
        
        return self.repo.get_by_id(plugin_id)
    
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
