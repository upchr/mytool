# -*- coding: utf-8 -*-
"""dianbiao 模块 - Pydantic 数据模型"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReadingIn(BaseModel):
    """采集端上报的一条采样记录"""
    meter_id: str = Field(..., description="电表标识(SN)", min_length=3, max_length=64)
    ts: datetime = Field(..., description="采样时间(ISO8601, 采集端时钟)")
    name: Optional[str] = Field(None, description="电表别名(首次上报时用于自动注册)")
    status: str = "ok"
    surplus_value: Optional[float] = None
    total_value: Optional[float] = None
    power: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    pf: Optional[float] = None
    switch_status: Optional[int] = None
    order_value: Optional[float] = None
    soft_ver: Optional[int] = None
    protocol_ver: Optional[int] = None
    tx_msgid: Optional[int] = None
    raw: Optional[dict] = None


class ReadingOut(BaseModel):
    id: int
    meter_id: str
    ts: datetime
    status: str
    surplus_value: Optional[float] = None
    total_value: Optional[float] = None
    power: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    pf: Optional[float] = None
    switch_status: Optional[int] = None
    order_value: Optional[float] = None
    soft_ver: Optional[int] = None
    protocol_ver: Optional[int] = None


class MeterOut(BaseModel):
    meter_id: str
    name: Optional[str] = None
    mac: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class DailyStatOut(BaseModel):
    day: str
    total_value: Optional[float] = None
    surplus_value: Optional[float] = None
    power_avg: Optional[float] = None
    readings: int


class DailyStatsResp(BaseModel):
    meter_id: str
    days: List[DailyStatOut]


class TokenCreate(BaseModel):
    """创建推送 Token"""
    name: str = Field(..., description="用途备注, 例如: 客厅电表采集器", min_length=1, max_length=128)


class TokenOut(BaseModel):
    id: int
    token: str
    name: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class CollectorConfigIn(BaseModel):
    """前端保存某台采集器的运行配置(mytool 反向下发)"""
    meter_id: str = Field(..., min_length=3, max_length=64)
    interval_seconds: int = Field(..., ge=30, le=86400, description="采集间隔秒")
    enabled: int = Field(1, ge=0, le=1, description="1=正常采集 0=暂停采集")


class TriggerCreate(BaseModel):
    """搭建采集器触发器(所属节点 + 目录位置)"""
    node_id: int = Field(..., gt=0, description="目标节点(nodes.id)")
    work_dir: str = Field(..., min_length=1, max_length=512, description="节点上采集器工程目录")
    source_dir: Optional[str] = Field(None, max_length=512, description="mytool 侧代码源目录(为空用后端默认)")
    meter_id: Optional[str] = Field(None, min_length=3, max_length=64, description="采集器 SN(YM_SN, 留空初始化自动识别)")
    ym_mac: Optional[str] = Field(None, max_length=64, description="BLE MAC(YM_MAC, 初始化写入节点 .env)")
    agent_token: Optional[str] = Field(None, max_length=128, description="上报 Token(MYTOOL_AGENT_TOKEN, 留空初始化自动创建)")
    mytool_url: Optional[str] = Field(None, max_length=256, description="mytool 后端地址(MYTOOL_URL, 留空初始化自动推断)")
    name: Optional[str] = Field(None, max_length=128, description="触发器名称")
    interval_seconds: int = Field(300, ge=30, le=86400, description="采集间隔秒")
    enabled: int = Field(1, ge=0, le=1, description="1=运行 0=停采")


class TriggerUpdate(BaseModel):
    """更新触发器(保存即反推配置到采集器)"""
    name: Optional[str] = Field(None, max_length=128)
    work_dir: Optional[str] = Field(None, min_length=1, max_length=512)
    source_dir: Optional[str] = Field(None, max_length=512)
    meter_id: Optional[str] = Field(None, min_length=3, max_length=64, description="采集器 SN, 传空字符串可清空")
    ym_mac: Optional[str] = Field(None, max_length=64, description="BLE MAC, 传空字符串可清空")
    agent_token: Optional[str] = Field(None, max_length=128, description="上报 Token, 传空字符串可清空")
    mytool_url: Optional[str] = Field(None, max_length=256, description="mytool 后端地址, 传空字符串可清空")
    interval_seconds: Optional[int] = Field(None, ge=30, le=86400)
    enabled: Optional[int] = Field(None, ge=0, le=1)


class AlertCreate(BaseModel):
    """新增阈值告警规则(指标 + 阈值 + 通知渠道)"""
    meter_id: str = Field(..., min_length=3, max_length=64, description="电表标识(SN)")
    metric: str = Field(..., description="指标: surplus_value/total_value/power/voltage/current")
    condition: str = Field("lt", description="lt=低于 gt=高于")
    threshold: float = Field(..., description="告警阈值")
    service_id: int = Field(..., gt=0, description="通知渠道(notification_services.id, 须已启用)")
    cooldown_minutes: int = Field(10, ge=1, le=1440, description="冷却(分钟), 命中后多久内不再重复告警")
    enabled: int = Field(1, ge=0, le=1)


class AlertUpdate(BaseModel):
    """更新阈值告警规则"""
    meter_id: Optional[str] = Field(None, min_length=3, max_length=64)
    metric: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    service_id: Optional[int] = Field(None, gt=0)
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    enabled: Optional[int] = Field(None, ge=0, le=1)