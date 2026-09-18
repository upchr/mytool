# -*- coding: utf-8 -*-
"""dianbiao 模块 - 数据模型

远蓝/云瞄预付费电表读数采集:
  dianbiao_meters     电表设备(首次上报自动注册)
  dianbiao_readings   采样数据(按 meter_id+ts 幂等, 重复上报不产生重复行)
"""
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from app.core.db.database import metadata


# 采集端推送 Token(浏览器面板维护, 可创建/作废; 不写入项目配置)
dianbiao_token_table = Table(
    "dianbiao_token",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("token", String(64), nullable=False, comment="推送令牌(明文, 仅此一处可查看)"),
    Column("name", String(128), comment="用途备注, 便于识别采集端"),
    Column("status", String(16), default="active", comment="active/revoked"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    Column("revoked_at", DateTime, comment="作废时间"),
    Column("last_used_at", DateTime, comment="最近一次上报使用时间"),
    UniqueConstraint("token", name="uq_dianbiao_token"),
    sqlite_autoincrement=True,
)


# 电表设备表
dianbiao_meter_table = Table(
    "dianbiao_meter",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meter_id", String(64), nullable=False, comment="仪表标识(SN)"),
    Column("name", String(128), comment="名称/备注"),
    Column("mac", String(32), comment="BLE MAC"),
    Column("first_seen", DateTime, default=datetime.now, comment="首次上报时间"),
    Column("last_seen", DateTime, default=datetime.now, onupdate=datetime.now, comment="最后上报时间"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    UniqueConstraint("meter_id", name="uq_dianbiao_meter_id"),
    sqlite_autoincrement=True,
)

# 采集器运行配置(mytool 反向下发, 采集端每轮拉取; meter_id 未配置时用后端默认值)
dianbiao_collector_config_table = Table(
    "dianbiao_collector_config",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meter_id", String(64), nullable=False, comment="采集器标识(SN)"),
    Column("interval_seconds", Integer, nullable=False, default=300, comment="采集间隔秒"),
    Column("enabled", Integer, nullable=False, default=1, comment="1=正常采集 0=暂停采集"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment="最后修改时间"),
    UniqueConstraint("meter_id", name="uq_dianbiao_collector_config_meter"),
    sqlite_autoincrement=True,
)

# 采集器部署触发器(mytool 面板搭建: 所属节点 + 目录位置 + 初始化(远端 doctor) + 反推配置)
dianbiao_trigger_table = Table(
    "dianbiao_trigger",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(128), comment="触发器名称"),
    Column("node_id", Integer, nullable=False, comment="所属节点(nodes.id)"),
    Column("node_host", String(128), comment="节点地址快照(展示用)"),
    Column("work_dir", String(512), comment="目标节点上采集器工程目录"),
    Column("source_dir", String(512), comment="mytool 侧代码源目录(初始化时打包上传, 不含 .env)"),
    Column("meter_id", String(64), comment="目标采集器标识(SN, 初始化时从 .env 读取)"),
    Column("ym_mac", String(64), comment="BLE MAC(初始化时写入节点 .env 的 YM_MAC)"),
    Column("agent_token", String(128), comment="上报 Token(初始化时写入 .env 的 MYTOOL_AGENT_TOKEN, 为空自动创建)"),
    Column("mytool_url", String(256), comment="mytool 后端地址(初始化时写入 .env 的 MYTOOL_URL, 为空自动推断)"),
    Column("interval_seconds", Integer, nullable=False, default=300, comment="采集间隔秒"),
    Column("enabled", Integer, nullable=False, default=1, comment="1=运行 0=停采"),
    Column("init_status", String(16), default="pending", comment="pending/ok/fail"),
    Column("init_output", Text, comment="最近一次 initialize(远端 doctor)输出"),
    Column("init_at", DateTime, comment="最近一次初始化时间"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"),
    sqlite_autoincrement=True,
)

# 阈值告警规则(读取上报时评估, 命中后经通知渠道推送)
dianbiao_alert_table = Table(
    "dianbiao_alert",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meter_id", String(64), nullable=False, comment="电表标识(SN)"),
    Column("metric", String(32), nullable=False, comment="指标: surplus_value/total_value/power/voltage/current"),
    Column("condition", String(4), nullable=False, default="lt", comment="lt=低于 gt=高于"),
    Column("threshold", Float, nullable=False, comment="告警阈值"),
    Column("service_id", Integer, nullable=False, comment="通知渠道(notification_services.id)"),
    Column("cooldown_minutes", Integer, nullable=False, default=10, comment="冷却(分钟), 命中后多久内不再重复告警"),
    Column("enabled", Integer, nullable=False, default=1, comment="1=启用 0=停用"),
    Column("last_alert_at", DateTime, comment="上次告警时间(用于冷却判断)"),
    Column("last_value", Float, comment="上次告警时的实际值"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"),
    sqlite_autoincrement=True,
)

# 充值记录(上报时自动识别: 剩余电量跳升 / 报文携带订单金额; 与读数表同时间戳幂等)
dianbiao_charge_table = Table(
    "dianbiao_charge",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meter_id", String(64), nullable=False, comment="电表标识(SN)"),
    Column("ts", DateTime, nullable=False, comment="识别所用上报时间(采集端时钟)"),
    Column("prev_value", Float, nullable=False, comment="充值前剩余电量(度)"),
    Column("new_value", Float, nullable=False, comment="充值后剩余电量(度)"),
    Column("delta", Float, nullable=False, comment="充值量(度): jump=剩余电量跳增, order=报文 order_value 增量"),
    Column("order_value", Float, comment="报文携带的 order_value 原值(首次出现作基线, 不作为事件)"),
    Column("mode", String(16), nullable=False, default="jump", comment="识别方式: jump=剩余跳变 order=结转单"),
    Column("created_at", DateTime, default=datetime.now, comment="创建时间"),
    UniqueConstraint("meter_id", "ts", name="uq_dianbiao_charge_meter_ts"),
    sqlite_autoincrement=True,
)

# 采样数据表
dianbiao_reading_table = Table(
    "dianbiao_reading",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meter_id", String(64), nullable=False, comment="电表标识(SN)"),
    Column("ts", DateTime, nullable=False, comment="采样时间(采集端时钟)"),
    Column("status", String(16), default="ok", comment="采样状态 ok/offline"),
    Column("surplus_value", Float, comment="剩余电量(度)"),
    Column("total_value", Float, comment="总用电量(度/kWh)"),
    Column("power", Float, comment="当前功率(W)"),
    Column("voltage", Float, comment="电压(V)"),
    Column("current", Float, comment="电流(A)"),
    Column("pf", Float, comment="功率因数"),
    Column("switch_status", Integer, comment="开关状态 1合/0分"),
    Column("order_value", Float, comment="报文携带的 order_value 原始值(累计值, 非单次充值)"),
    Column("soft_ver", Integer, comment="软件版本"),
    Column("protocol_ver", Integer, comment="协议版本"),
    Column("tx_msgid", Integer, comment="会话 txMsgId"),
    Column("raw", Text, comment="原始报文(JSON 保留字段)"),
    UniqueConstraint("meter_id", "ts", name="uq_dianbiao_meter_ts"),
    sqlite_autoincrement=True,
)

__all__ = ["dianbiao_meter_table", "dianbiao_reading_table", "dianbiao_token_table", "dianbiao_collector_config_table", "dianbiao_trigger_table", "dianbiao_alert_table"]