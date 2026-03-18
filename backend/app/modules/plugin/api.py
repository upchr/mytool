# app/modules/plugin/api.py
"""
插件模块 - FastAPI 路由定义

路由前缀: /plugins
标签: 插件管理
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.plugin import schemas
from app.modules.plugin.services import PluginService

router = APIRouter(prefix="/plugins", tags=["插件管理"])


@router.get("", response_model=BaseResponse[schemas.PluginListResponse])
async def list_plugins(
    plugin_type: Optional[str] = None,
    category: Optional[str] = None,
    is_official: Optional[bool] = None,
    is_installed: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    engine=Depends(get_engine)
):
    """
    获取插件列表
    
    Args:
        plugin_type: 插件类型筛选
        category: 分类筛选
        is_official: 是否官方筛选
        is_installed: 是否已安装筛选
        keyword: 关键词搜索
        page: 页码
        page_size: 每页大小
        engine: 数据库引擎
    
    Returns:
        分页插件列表
    """
    try:
        params = schemas.PluginQueryParams(
            plugin_type=plugin_type,
            category=category,
            is_official=is_official,
            is_installed=is_installed,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        service = PluginService(engine)
        result = service.get_list(params)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{plugin_id}", response_model=BaseResponse[schemas.PluginRead])
async def get_plugin(
    plugin_id: str,
    engine=Depends(get_engine)
):
    """
    获取插件详情
    
    Args:
        plugin_id: 插件ID
        engine: 数据库引擎
    
    Returns:
        插件数据
    """
    service = PluginService(engine)
    result = service.get_by_id(plugin_id)
    if not result:
        return BaseResponse.error(404, f"插件不存在: {plugin_id}")
    return BaseResponse.success(result)


@router.post("", response_model=BaseResponse[schemas.PluginRead])
async def create_plugin(
    data: schemas.PluginCreate,
    engine=Depends(get_engine)
):
    """
    创建插件
    
    Args:
        data: 创建数据
        engine: 数据库引擎
    
    Returns:
        创建后的插件数据
    """
    try:
        service = PluginService(engine)
        existing = service.get_by_id(data.plugin_id)
        if existing:
            return BaseResponse.error(400, f"插件ID已存在: {data.plugin_id}")
        
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.put("/{plugin_id}", response_model=BaseResponse[schemas.PluginRead])
async def update_plugin(
    plugin_id: str,
    data: schemas.PluginUpdate,
    engine=Depends(get_engine)
):
    """
    更新插件
    
    Args:
        plugin_id: 插件ID
        data: 更新数据
        engine: 数据库引擎
    
    Returns:
        更新后的插件数据
    """
    try:
        service = PluginService(engine)
        existing = service.get_by_id(plugin_id)
        if not existing:
            return BaseResponse.error(404, f"插件不存在: {plugin_id}")
        
        result = service.update(plugin_id, data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    engine=Depends(get_engine)
):
    """
    删除插件（软删除）
    
    Args:
        plugin_id: 插件ID
        engine: 数据库引擎
    
    Returns:
        操作结果
    """
    try:
        service = PluginService(engine)
        existing = service.get_by_id(plugin_id)
        if not existing:
            return BaseResponse.error(404, f"插件不存在: {plugin_id}")
        
        # 软删除：设置为不启用
        service.update(plugin_id, schemas.PluginUpdate(is_active=False))
        return BaseResponse.success(message="删除成功")
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    config: Optional[dict] = None,
    engine=Depends(get_engine)
):
    """
    安装插件
    
    Args:
        plugin_id: 插件ID
        config: 插件配置
        engine: 数据库引擎
    
    Returns:
        安装后的插件数据
    """
    try:
        service = PluginService(engine)
        result = service.install(plugin_id, config)
        return BaseResponse.success(result, message="插件安装成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(
    plugin_id: str,
    engine=Depends(get_engine)
):
    """
    卸载插件
    
    Args:
        plugin_id: 插件ID
        engine: 数据库引擎
    
    Returns:
        卸载后的插件数据
    """
    try:
        service = PluginService(engine)
        result = service.uninstall(plugin_id)
        return BaseResponse.success(result, message="插件卸载成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{plugin_id}/configs")
async def get_plugin_configs(
    plugin_id: str,
    engine=Depends(get_engine)
):
    """
    获取插件配置
    
    Args:
        plugin_id: 插件ID
        engine: 数据库引擎
    
    Returns:
        插件配置列表
    """
    service = PluginService(engine)
    plugin = service.get_by_id(plugin_id)
    if not plugin:
        return BaseResponse.error(404, f"插件不存在: {plugin_id}")
    
    result = service.get_configs(plugin_id)
    return BaseResponse.success(result)
