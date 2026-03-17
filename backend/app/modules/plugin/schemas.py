from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== 插件 ==============

class PluginBase(BaseModel):
    plugin_id: str = Field(..., description="插件唯一标识")
    name: str = Field(..., description="插件名称")
    version: str = Field(default="1.0.0", description="插件版本")
    author: str = Field(default="MyTool Team", description="作者")
    description: Optional[str] = Field(None, description="插件描述")
    plugin_type: str = Field(..., description="插件类型")
    category: Optional[str] = Field(None, description="分类")
    entry_point: str = Field(..., description="入口点")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    icon: Optional[str] = Field(None, description="图标")
    homepage: Optional[str] = Field(None, description="主页链接")
    repository: Optional[str] = Field(None, description="仓库链接")
    license: Optional[str] = Field(None, description="许可证")
    is_official: bool = Field(default=False, description="是否官方")
    is_enabled: bool = Field(default=True, description="是否启用")


class PluginCreate(PluginBase):
    pass


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    permissions: Optional[List[str]] = None
    icon: Optional[str] = None
    is_enabled: Optional[bool] = None


class Plugin(PluginBase):
    id: int
    is_installed: bool = False
    download_count: int = 0
    rating_count: int = 0
    rating_avg: int = 0
    installed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 插件配置 ==============

class PluginConfigBase(BaseModel):
    plugin_id: str
    config_key: str = Field(..., description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field(default="string", description="配置类型")
    is_secret: bool = Field(default=False, description="是否加密")


class PluginConfigCreate(PluginConfigBase):
    pass


class PluginConfig(PluginConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 评分 ==============

class PluginRatingBase(BaseModel):
    plugin_id: str
    user_id: int
    rating: int = Field(..., ge=1, le=5, description="评分1-5")
    comment: Optional[str] = Field(None, description="评论")


class PluginRatingCreate(PluginRatingBase):
    pass


class PluginRating(PluginRatingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 查询参数 ==============

class PluginQueryParams(BaseModel):
    plugin_type: Optional[str] = None
    category: Optional[str] = None
    is_official: Optional[bool] = None
    is_installed: Optional[bool] = None
    keyword: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ============== 插件操作 ==============

class PluginInstallRequest(BaseModel):
    plugin_id: str = Field(..., description="插件ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="插件配置")


class PluginCallRequest(BaseModel):
    plugin_id: str = Field(..., description="插件ID")
    method: str = Field(..., description="调用方法")
    params: Dict[str, Any] = Field(default_factory=dict, description="方法参数")
