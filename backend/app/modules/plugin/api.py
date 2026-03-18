# app/modules/plugin/api.py
"""
插件模块 - FastAPI 路由定义

路由前缀: /plugins
标签: 插件管理

注意：具名路由要放在动态路由（/{id}）前面，防止路由匹配失效
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel, Field

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.plugin import schemas
from app.modules.plugin.services import PluginService

router = APIRouter(prefix="/plugins", tags=["插件管理"])


# ========== 请求 Schema ==========

class NotificationRequest(BaseModel):
    """通知请求"""
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")


class ExecuteRequest(BaseModel):
    """执行请求"""
    command: str = Field(..., description="要执行的命令")
    timeout: Optional[int] = Field(300, description="超时时间（秒）")


# ========== 插件管理接口 ==========

@router.post("", response_model=BaseResponse[schemas.PluginRead])
async def create_plugin(
    data: schemas.PluginCreate,
    engine=Depends(get_engine)
):
    """创建插件"""
    try:
        service = PluginService(engine)
        existing = service.get_by_id(data.plugin_id)
        if existing:
            return BaseResponse.error(400, f"插件ID已存在: {data.plugin_id}")
        
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


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
    """获取插件列表"""
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


# ========== 插件操作接口（动态路由前面，按路径深度排序） ==========

@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    config: Optional[dict] = None,
    engine=Depends(get_engine)
):
    """安装插件"""
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
    """卸载插件"""
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
    """获取插件配置"""
    service = PluginService(engine)
    plugin = service.get_by_id(plugin_id)
    if not plugin:
        return BaseResponse.error(404, f"插件不存在: {plugin_id}")
    
    result = service.get_configs(plugin_id)
    return BaseResponse.success(result)


@router.post("/{plugin_id}/send")
async def send_notification(
    plugin_id: str,
    data: NotificationRequest,
    engine=Depends(get_engine)
):
    """发送通知（通知类插件专用）"""
    try:
        service = PluginService(engine)
        success = service.send_notification(plugin_id, data.title, data.content)
        if success:
            return BaseResponse.success(message="通知发送成功")
        return BaseResponse.error(500, "通知发送失败")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/{plugin_id}/execute")
async def execute_command(
    plugin_id: str,
    data: ExecuteRequest,
    engine=Depends(get_engine)
):
    """执行命令（执行器类插件专用）"""
    try:
        service = PluginService(engine)
        result = service.execute_command(plugin_id, data.command, timeout=data.timeout)
        return BaseResponse.success(result)
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


# ========== 插件 CRUD（动态路由放在最后） ==========

@router.get("/{plugin_id}", response_model=BaseResponse[schemas.PluginRead])
async def get_plugin(
    plugin_id: str,
    engine=Depends(get_engine)
):
    """获取插件详情"""
    service = PluginService(engine)
    result = service.get_by_id(plugin_id)
    if not result:
        return BaseResponse.error(404, f"插件不存在: {plugin_id}")
    return BaseResponse.success(result)


@router.put("/{plugin_id}", response_model=BaseResponse[schemas.PluginRead])
async def update_plugin(
    plugin_id: str,
    data: schemas.PluginUpdate,
    engine=Depends(get_engine)
):
    """更新插件"""
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
    """删除插件（软删除）"""
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


@router.post("/init")
async def init_plugins(engine=Depends(get_engine)):
    """
    初始化内置插件
    
    将官方预置的插件写入数据库，包括：
    - 飞书通知：通过飞书群机器人发送消息
    - 钉钉通知：通过钉钉群机器人发送消息（支持加签）
    - 企业微信通知：通过企业微信机器人发送消息
    - Bark通知：发送 iOS 推送通知
    - 本地执行器：在本地执行 Shell 命令
    
    Args:
        engine: 数据库引擎
    
    Returns:
        初始化结果
    """
    try:
        service = PluginService(engine)
        service.init_builtin_plugins()
        return BaseResponse.success(message="内置插件初始化成功")
    except Exception as e:
        return BaseResponse.error(500, str(e))
