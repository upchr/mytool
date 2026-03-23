"""
CPE 模块 - API 路由

烽火 5G CPE 路由器管理接口
"""

from fastapi import APIRouter, Depends, Query
from app.core.db.database import get_engine
from app.core.pojo.response import BaseResponse
from app.core.exception.exceptions import NotFoundException, ServerException

from . import schemas, services

router = APIRouter(prefix="/cpe", tags=["CPE 设备管理"])


# ==================== 配置管理 ====================

@router.post("/configs", response_model=BaseResponse[schemas.CPEConfigRead])
async def create_config(data: schemas.CPEConfigCreate, engine=Depends(get_engine)):
    """
    创建 CPE 配置
    
    Args:
        data: 配置数据
    
    Returns:
        创建的配置
    """
    service = services.CPEConfigService(engine)
    result = service.create(data.model_dump())
    
    # 如果启用了自动监控，自动启动监控
    if result.get("auto_monitor") and result.get("is_active"):
        services.CPEMonitorService.start_monitor(result)
    
    return BaseResponse.success(result)


@router.get("/configs")
async def get_configs(active_only: bool = False, engine=Depends(get_engine)):
    """
    获取配置列表
    
    Args:
        active_only: 仅返回启用的配置
    
    Returns:
        配置列表
    """
    service = services.CPEConfigService(engine)
    result = service.get_all(active_only)
    return BaseResponse.success(result)


@router.get("/configs/{config_id}", response_model=BaseResponse[schemas.CPEConfigRead])
async def get_config(config_id: int, engine=Depends(get_engine)):
    """
    获取单个配置
    
    Args:
        config_id: 配置 ID
    """
    service = services.CPEConfigService(engine)
    result = service.get_by_id(config_id)
    if not result:
        raise NotFoundException(detail="配置不存在")
    return BaseResponse.success(result)


@router.put("/configs/{config_id}", response_model=BaseResponse[schemas.CPEConfigRead])
async def update_config(config_id: int, data: schemas.CPEConfigUpdate, engine=Depends(get_engine)):
    """
    更新配置
    
    Args:
        config_id: 配置 ID
        data: 更新数据
    """
    service = services.CPEConfigService(engine)
    result = service.update(config_id, data.model_dump(exclude_unset=True))
    if not result:
        raise NotFoundException(detail="配置不存在")
    
    # 检查是否需要启动/停止监控
    if data.auto_monitor is not None:
        if data.auto_monitor and result.get("is_active"):
            # 启用自动监控，启动监控
            services.CPEMonitorService.start_monitor(result)
        elif not data.auto_monitor:
            # 禁用自动监控，如果当前正在监控这个配置，则停止
            status = services.CPEMonitorService.get_status()
            if status.get("config_id") == config_id:
                services.CPEMonitorService.stop_monitor()
    
    return BaseResponse.success(result)


@router.delete("/configs/{config_id}")
async def delete_config(config_id: int, engine=Depends(get_engine)):
    """
    删除配置
    
    Args:
        config_id: 配置 ID
    """
    service = services.CPEConfigService(engine)
    success = service.delete(config_id)
    if not success:
        raise NotFoundException(detail="配置不存在")
    return BaseResponse.success(message="删除成功")


@router.patch("/configs/{config_id}/toggle")
async def toggle_config(config_id: int, is_active: bool = True, engine=Depends(get_engine)):
    """
    切换配置启用状态
    
    Args:
        config_id: 配置 ID
        is_active: 是否启用
    """
    service = services.CPEConfigService(engine)
    success = service.toggle_status(config_id, is_active)
    if not success:
        raise NotFoundException(detail="配置不存在")
    return BaseResponse.success({"is_active": is_active})


# ==================== 设备信息 ====================

@router.post("/test")
async def test_connection(data: schemas.CPEConfigCreate, engine=Depends(get_engine)):
    """
    测试连接
    
    测试 CPE 设备连接是否正常
    """
    result = services.CPEClientService.test_connection(
        data.host,
        data.username,
        data.password
    )
    
    if result["success"]:
        return BaseResponse.success(result)
    else:
        return BaseResponse.error(400, result["message"])


@router.get("/configs/{config_id}/device")
async def get_device_info(config_id: int, engine=Depends(get_engine)):
    """
    获取设备信息
    
    获取 CPE 设备的详细信息（型号、序列号、温度、运行时间等）
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    result = services.CPEClientService.get_device_info(
        config["host"],
        config["username"],
        config["password"]
    )
    
    if result["success"]:
        return BaseResponse.success(result["data"])
    else:
        return BaseResponse.error(400, result["message"])


@router.get("/configs/{config_id}/temperature")
async def get_temperature(config_id: int, engine=Depends(get_engine)):
    """
    获取温度
    
    获取 CPE 设备的 5G/4G 模块温度
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    result = services.CPEClientService.get_device_info(
        config["host"],
        config["username"],
        config["password"]
    )
    
    if result["success"]:
        return BaseResponse.success(result["data"].get("temperature", {}))
    else:
        return BaseResponse.error(400, result["message"])


@router.get("/configs/{config_id}/signal")
async def get_signal_info(config_id: int, engine=Depends(get_engine)):
    """
    获取信号信息
    
    获取 CPE 设备的信号强度信息（RSRP、RSSI、SINR等）
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    from .lib.client import CPEClient
    
    client = CPEClient(config["host"], config["username"], config["password"])
    success, msg = client.login()
    
    if not success:
        return BaseResponse.error(400, msg)
    
    try:
        signal = client.get_signal_info()
        return BaseResponse.success(signal)
    finally:
        client.logout()


@router.get("/configs/{config_id}/traffic")
async def get_traffic_stats(config_id: int, engine=Depends(get_engine)):
    """
    获取流量统计
    
    获取 CPE 设备的流量使用情况
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    from .lib.client import CPEClient
    
    client = CPEClient(config["host"], config["username"], config["password"])
    success, msg = client.login()
    
    if not success:
        return BaseResponse.error(400, msg)
    
    try:
        traffic = client.get_traffic_stats()
        return BaseResponse.success(traffic)
    finally:
        client.logout()


# ==================== 短信管理 ====================

@router.get("/configs/{config_id}/sms")
async def get_sms_list(config_id: int, limit: int = 20, engine=Depends(get_engine)):
    """
    获取短信列表
    
    获取 CPE 设备上的短信列表
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    result = services.CPEClientService.get_sms_list(
        config["host"],
        config["username"],
        config["password"],
        limit
    )
    
    if result["success"]:
        return BaseResponse.success(result)
    else:
        return BaseResponse.error(400, result["message"])


@router.get("/configs/{config_id}/sms/unread")
async def get_unread_sms(config_id: int, engine=Depends(get_engine)):
    """
    获取未读短信
    
    获取 CPE 设备上的未读短信
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    from .lib.client import CPEClient
    
    client = CPEClient(config["host"], config["username"], config["password"])
    success, msg = client.login()
    
    if not success:
        return BaseResponse.error(400, msg)
    
    try:
        sms_list = client.get_unread_sms()
        return BaseResponse.success({"total": len(sms_list), "items": sms_list})
    finally:
        client.logout()


# ==================== 短信监控 ====================

@router.get("/monitor/status")
async def get_monitor_status():
    """
    获取监控状态
    
    获取短信监控的运行状态
    """
    status = services.CPEMonitorService.get_status()
    return BaseResponse.success(status)


@router.post("/monitor/start/{config_id}")
async def start_monitor(config_id: int, engine=Depends(get_engine)):
    """
    启动监控
    
    启动短信监控，自动转发新短信
    """
    config_service = services.CPEConfigService(engine)
    config = config_service.get_by_id(config_id)
    
    if not config:
        raise NotFoundException(detail="配置不存在")
    
    success = services.CPEMonitorService.start_monitor(config)
    
    if success:
        return BaseResponse.success(message=f"监控已启动: {config['name']}")
    else:
        return BaseResponse.error(400, "监控已在运行中")


@router.post("/monitor/stop")
async def stop_monitor():
    """
    停止监控
    
    停止短信监控
    """
    services.CPEMonitorService.stop_monitor()
    return BaseResponse.success(message="监控已停止")
