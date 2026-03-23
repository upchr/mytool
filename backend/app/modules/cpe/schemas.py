"""
CPE 模块 - Pydantic 模式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================== CPE 配置 ====================

class CPEConfigBase(BaseModel):
    """CPE 配置基础 Schema"""
    name: str = Field(..., description="配置名称", min_length=1, max_length=100)
    host: str = Field(..., description="CPE 地址", min_length=1, max_length=255)
    username: str = Field("admin", description="用户名", max_length=100)
    password: str = Field(..., description="密码", min_length=1, max_length=255)
    is_active: bool = Field(True, description="是否启用")
    auto_monitor: bool = Field(False, description="自动监控短信")
    check_interval: float = Field(3.0, description="检查间隔(秒)")
    # 通知配置
    bark_key: Optional[str] = Field(None, description="Bark 推送 Key", max_length=255)
    bark_server: str = Field("https://api.day.app", description="Bark 服务器", max_length=255)
    feishu_webhook: Optional[str] = Field(None, description="飞书 Webhook URL", max_length=500)
    webhook_url: Optional[str] = Field(None, description="自定义 Webhook URL", max_length=500)


class CPEConfigCreate(CPEConfigBase):
    """创建 CPE 配置"""
    pass


class CPEConfigUpdate(BaseModel):
    """更新 CPE 配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    auto_monitor: Optional[bool] = None
    check_interval: Optional[float] = None
    bark_key: Optional[str] = Field(None, max_length=255)
    bark_server: Optional[str] = Field(None, max_length=255)
    feishu_webhook: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)


class CPEConfigRead(CPEConfigBase):
    """读取 CPE 配置"""
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== 设备信息 ====================

class DeviceInfo(BaseModel):
    """设备信息"""
    product_name: str = Field("5G CPE", description="产品名称")
    model_name: str = Field("", description="设备型号")
    serial_number: str = Field("", description="序列号")
    mac_address: str = Field("", description="MAC 地址")
    software_version: str = Field("", description="软件版本")
    hardware_version: str = Field("", description="硬件版本")
    uptime: Optional[Dict[str, int]] = Field(None, description="运行时间")
    temperature: Optional[Dict[str, Any]] = Field(None, description="温度")


class TemperatureInfo(BaseModel):
    """温度信息"""
    temp_5g: float = Field(0, description="5G 温度(℃)")
    temp_4g: Optional[float] = Field(None, description="4G 温度(℃)")


class SystemUsage(BaseModel):
    """系统使用率"""
    cpu: Optional[float] = Field(None, description="CPU 使用率(%)")
    memory: Optional[float] = Field(None, description="内存使用率(%)")


class SignalInfo(BaseModel):
    """信号信息"""
    rsrp: Optional[str] = Field(None, description="RSRP")
    rssi: Optional[str] = Field(None, description="RSSI")
    sinr: Optional[str] = Field(None, description="SINR")
    band: Optional[str] = Field(None, description="频段")


class TrafficStats(BaseModel):
    """流量统计"""
    today_tx: Optional[int] = Field(None, description="今日发送(字节)")
    today_rx: Optional[int] = Field(None, description="今日接收(字节)")
    month_tx: Optional[int] = Field(None, description="本月发送(字节)")
    month_rx: Optional[int] = Field(None, description="本月接收(字节)")


# ==================== 短信 ====================

class SMSMessage(BaseModel):
    """短信消息"""
    id: str = Field("", description="短信 ID")
    phone: str = Field("", description="短信号码")
    content: str = Field("", description="短信内容")
    time: str = Field("", description="接收时间")
    is_read: bool = Field(False, description="是否已读")
    is_sent: bool = Field(False, description="是否发送")


class SMSListResponse(BaseModel):
    """短信列表响应"""
    total: int
    items: List[SMSMessage]


# ==================== 监控状态 ====================

class MonitorStatus(BaseModel):
    """监控状态"""
    running: bool = Field(False, description="是否运行中")
    config_id: Optional[int] = Field(None, description="当前监控的配置 ID")
    config_name: Optional[str] = Field(None, description="配置名称")
    check_interval: float = Field(3.0, description="检查间隔")
    last_check: Optional[datetime] = Field(None, description="上次检查时间")
    total_sms: int = Field(0, description="已接收短信总数")
