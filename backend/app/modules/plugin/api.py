from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from .schemas import (
    Plugin,
    PluginCreate,
    PluginUpdate,
    PluginConfig,
    PluginConfigCreate,
    PluginRating,
    PluginRatingCreate,
    PluginQueryParams,
    PluginInstallRequest,
    PluginCallRequest
)
from .services import PluginService

router = APIRouter(prefix="/plugins", tags=["插件系统"])


@router.get("", response_model=List[Plugin])
async def list_plugins(
    plugin_type: Optional[str] = None,
    category: Optional[str] = None,
    is_official: Optional[bool] = None,
    is_installed: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取插件列表"""
    params = PluginQueryParams(
        plugin_type=plugin_type,
        category=category,
        is_official=is_official,
        is_installed=is_installed,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    plugins, total = await PluginService.list_plugins(params)
    return plugins


@router.get("/{plugin_id}", response_model=Plugin)
async def get_plugin(plugin_id: str):
    """获取插件详情"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return plugin


@router.post("", response_model=Plugin)
async def create_plugin(data: PluginCreate):
    """创建插件"""
    existing = await PluginService.get_plugin(data.plugin_id)
    if existing:
        raise HTTPException(status_code=400, detail="插件ID已存在")
    return await PluginService.create_plugin(data)


@router.put("/{plugin_id}", response_model=Plugin)
async def update_plugin(plugin_id: str, data: PluginUpdate):
    """更新插件"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return await PluginService.update_plugin(plugin_id, data)


@router.delete("/{plugin_id}")
async def delete_plugin(plugin_id: str):
    """删除插件"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    await PluginService.delete_plugin(plugin_id)
    return {"message": "删除成功"}


@router.post("/{plugin_id}/install")
async def install_plugin(plugin_id: str, data: PluginInstallRequest):
    """安装插件"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    result = await PluginService.install_plugin(plugin_id, data.config)
    return {"message": "安装成功", "plugin": result}


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str):
    """卸载插件"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    result = await PluginService.uninstall_plugin(plugin_id)
    return {"message": "卸载成功", "plugin": result}


@router.post("/{plugin_id}/load")
async def load_plugin(plugin_id: str):
    """加载插件"""
    plugin_instance = await PluginService.load_plugin(plugin_id)
    if not plugin_instance:
        raise HTTPException(status_code=400, detail="插件加载失败")
    return {"message": "加载成功"}


@router.post("/call")
async def call_plugin(data: PluginCallRequest):
    """调用插件方法"""
    try:
        result = await PluginService.call_plugin(data.plugin_id, data.method, data.params)
        return {"message": "调用成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plugin_id}/configs", response_model=List[PluginConfig])
async def get_plugin_configs(plugin_id: str):
    """获取插件配置"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return await PluginService.get_configs(plugin_id)


@router.post("/{plugin_id}/configs", response_model=PluginConfig)
async def set_plugin_config(plugin_id: str, data: PluginConfigCreate):
    """设置插件配置"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    await PluginService.set_config(
        plugin_id,
        data.config_key,
        data.config_value or "",
        data.config_type,
        data.is_secret
    )
    # 返回所有配置
    configs = await PluginService.get_configs(plugin_id)
    return next((c for c in configs if c["config_key"] == data.config_key), None)


@router.post("/{plugin_id}/ratings", response_model=PluginRating)
async def rate_plugin(plugin_id: str, data: PluginRatingCreate):
    """给插件评分"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    data.plugin_id = plugin_id
    return await PluginService.create_rating(data)


@router.post("/{plugin_id}/reload")
async def reload_plugin(plugin_id: str, force: bool = True):
    """热重载插件"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    plugin_instance = await PluginService.load_plugin(plugin_id, force_reload=force)
    if not plugin_instance:
        raise HTTPException(status_code=400, detail="插件重载失败")
    
    return {"message": "重载成功"}


@router.get("/{plugin_id}/sandbox/log")
async def get_plugin_sandbox_log(plugin_id: str, limit: int = Query(100, ge=1, le=1000)):
    """获取插件沙箱操作日志"""
    plugin = await PluginService.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    sandbox = PluginService._plugin_sandboxes.get(plugin_id)
    if not sandbox:
        return {"logs": []}
    
    return {"logs": sandbox.get_operation_log(limit)}
