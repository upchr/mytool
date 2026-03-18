# app/modules/plugin/schemas.py
"""
插件模块 - Pydantic Schema 定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== 插件相关 Schema ==========

class PluginBase(BaseModel):
    """插件基础 Schema"""
    plugin_id: str = Field(..., description="插件唯一标识", min_length=1, max_length=100)
    name: str = Field(..., description="插件名称", min_length=1, max_length=100)
    version: str = Field("1.0.0", description="版本号")
    author: str = Field("MyTool Team", description="作者")
    description: Optional[str] = Field(None, description="插件描述")
    plugin_type: Optional[str] = Field(None, description="插件类型")
    category: Optional[str] = Field(None, description="分类")
    icon: Optional[str] = Field(None, description="图标")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    entry_point: Optional[str] = Field(None, description="入口点")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    is_official: bool = Field(True, description="是否官方插件")
    is_active: bool = Field(True, description="是否启用")


class PluginCreate(PluginBase):
    """创建插件"""
    pass


class PluginUpdate(BaseModel):
    """更新插件"""
    name: Optional[str] = Field(None, description="插件名称")
    version: Optional[str] = Field(None, description="版本号")
    description: Optional[str] = Field(None, description="插件描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PluginRead(PluginBase):
    """插件读取 Schema"""
    id: int
    is_installed: bool
    download_count: int
    rating_count: int
    rating_avg: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PluginListResponse(BaseModel):
    """插件列表响应"""
    total: int
    page: int
    page_size: int
    items: List[PluginRead]


# ========== 插件配置相关 Schema ==========

class PluginConfigBase(BaseModel):
    """插件配置基础 Schema"""
    plugin_id: str = Field(..., description="插件ID")
    config_key: str = Field(..., description="配置键", min_length=1, max_length=100)
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field("string", description="配置类型")
    is_secret: bool = Field(False, description="是否敏感信息")


class PluginConfigCreate(PluginConfigBase):
    """创建插件配置"""
    pass


class PluginConfigRead(PluginConfigBase):
    """插件配置读取 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ========== 查询参数 ==========

class PluginQueryParams(BaseModel):
    """插件查询参数"""
    plugin_type: Optional[str] = Field(None, description="插件类型")
    category: Optional[str] = Field(None, description="分类")
    is_official: Optional[bool] = Field(None, description="是否官方")
    is_installed: Optional[bool] = Field(None, description="是否已安装")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


__all__ = [
    "PluginBase",
    "PluginCreate",
    "PluginUpdate",
    "PluginRead",
    "PluginListResponse",
    "PluginConfigBase",
    "PluginConfigCreate",
    "PluginConfigRead",
    "PluginQueryParams",
]
