// 电表采集 API 客户端
// 后端: /dianbiao/* (见 backend/app/modules/dianbiao/api.py)

export interface MeterInfo {
  meter_id: string
  name?: string
  first_seen?: string
  last_seen?: string
}

export interface Reading {
  id: number
  meter_id: string
  ts: string
  status: string
  surplus_value?: number | null   // 剩余金额或剩余度数(取决于表计参数)
  total_value?: number | null     // 累计电量(度)
  power?: number | null           // 当前功率 W
  voltage?: number | null         // 电压 V
  current?: number | null         // 电流 A
  pf?: number | null              // 功率因数
  switch_status?: number | null   // 1 合闸 0 拉闸
  order_value?: number | null
  soft_ver?: number | null
  protocol_ver?: number | null
  tx_msgid?: number | null
}

export interface DailyStat {
  bucket: string
  usage: number | null   // 区间用电增量(度)
  power_avg: number | null
  readings: number
}

export type StatsBucket = 'day' | 'week' | 'month' | 'quarter' | 'year'

/** 电表设备列表 */
export const getMeters = () => window.$request.get('/dianbiao/meters') as Promise<MeterInfo[]>

/** 最新一条读数 */
export const getLatest = (meterId: string) =>
  window.$request.get('/dianbiao/latest', { params: { meter_id: meterId } }) as Promise<Reading | null>

/** 时间范围读数(画曲线用) */
export const getReadings = (meterId: string, hours = 24, limit = 5000) =>
  window.$request.get('/dianbiao/readings', {
    params: { meter_id: meterId, hours, limit }
  }) as Promise<Reading[]>

/** 聚合统计(日/周/月/季/年; 提供 start 则窗口=[start,现在], 否则回溯 days) */
export const getStats = (meterId: string, bucket: StatsBucket = 'day', days?: number, start?: string) =>
  window.$request.get('/dianbiao/stats', {
    params: {
      meter_id: meterId,
      bucket,
      ...(days ? { days } : {}),
      ...(start ? { start } : {}),
    }
  }) as Promise<{ meter_id: string; bucket: StatsBucket; days: DailyStat[] }>

// ---------- 采集器运行配置(mytool 反向下发) ----------

export interface CollectorConfig {
  meter_id: string
  name?: string
  last_seen?: string
  interval_seconds: number   // 采集间隔秒
  enabled: number            // 1=正常采集 0=暂停
  configured?: boolean
  updated_at?: string
}

/** 采集器配置列表 */
export const getCollectorConfigs = () =>
  window.$request.get('/dianbiao/collector-configs') as Promise<CollectorConfig[]>

/** 保存采集器配置(下发) */
export const saveCollectorConfig = (cfg: { meter_id: string; interval_seconds: number; enabled: number }) =>
  window.$request.put('/dianbiao/collector-configs', cfg) as Promise<{ meter_id: string; interval_seconds: number; enabled: number }>

// ---------- 采集器部署触发器(节点 + 目录 + 初始化/启停反推) ----------

export interface CollectorTrigger {
  id: number
  name?: string
  node_id: number
  node_name?: string
  node_host?: string
  work_dir?: string
  source_dir?: string
  meter_id?: string | null      // 采集器 SN(YM_SN)
  ym_mac?: string | null        // BLE MAC(YM_MAC)
  agent_token?: string | null   // 上报 Token(MYTOOL_AGENT_TOKEN)
  mytool_url?: string | null    // mytool 后端地址(MYTOOL_URL)
  interval_seconds: number
  enabled: number               // 1=运行 0=停采
  init_status?: 'pending' | 'ok' | 'fail'
  init_output?: string | null
  init_at?: string
  created_at?: string
  updated_at?: string
}

/** 触发器列表 */
export const getTriggeres = () =>
  window.$request.get('/dianbiao/triggers') as Promise<CollectorTrigger[]>

/** 搭建触发器 */
export const createTrigger = (data: { node_id: number; work_dir: string; source_dir?: string; meter_id?: string; ym_mac?: string; agent_token?: string; mytool_url?: string; name?: string; interval_seconds: number; enabled: number }) =>
  window.$request.post('/dianbiao/triggers', data) as Promise<{ id: string }>

/** 初始化触发器(代码分发 + 配置下发 + 远端 doctor → 反推基线配置, 可能耗时较长) */
export const initTrigger = (id: number) =>
  window.$request.post(`/dianbiao/triggers/${id}/init`, null, { timeout: 600000 }) as Promise<{ id: number; init_status: string; meter_id?: string; agent_token?: string; output: string }>

/** 更新触发器(启停/间隔/SN/MAC/Token, 自动反推采集器) */
export const updateTrigger = (id: number, data: Partial<{ name: string; work_dir: string; source_dir: string; meter_id: string; ym_mac: string; agent_token: string; mytool_url: string; interval_seconds: number; enabled: number }>) =>
  window.$request.put(`/dianbiao/triggers/${id}`, data) as Promise<{ id: number; pushed: boolean; proc?: string }>

/** 删除触发器 */
export const deleteTrigger = (id: number) =>
  window.$request.delete(`/dianbiao/triggers/${id}`) as Promise<{ id: number }>

// ---------- 推送 Token 维护(需 JWT) ----------

export interface PushToken {
  id: number
  token: string
  name?: string
  status: 'active' | 'revoked'
  created_at?: string
  revoked_at?: string
  last_used_at?: string
}

/** Token 列表 */
export const getTokens = () =>
  window.$request.get('/dianbiao/tokens') as Promise<PushToken[]>

/** 创建 Token */
export const createToken = (name: string) =>
  window.$request.post('/dianbiao/tokens', { name }) as Promise<PushToken>

/** 作废 Token */
export const revokeToken = (id: number) =>
  window.$request.post(`/dianbiao/tokens/${id}/revoke`) as Promise<{ id: number; status: string }>

// ---------- 阈值告警(复用「通知渠道」页已启用渠道) ----------

export interface NotifyService {
  id: number
  service_name: string
  service_type: string
}

export interface MeterAlert {
  id: number
  meter_id: string
  meter_name?: string
  metric: string               // surplus_value/total_value/power/voltage/current
  metric_label?: string
  condition: 'lt' | 'gt'      // lt=低于 gt=高于
  condition_label?: string
  threshold: number
  service_id: number          // 通知渠道 id
  service_name?: string
  cooldown_minutes: number    // 冷却(分钟)
  enabled: number             // 1=启用 0=停用
  last_alert_at?: string | null
  last_value?: number | null
  unit?: string
  created_at?: string
  updated_at?: string
}

/** 已启用的通知渠道(下拉用) */
export const getNotifyServices = () =>
  window.$request.get('/dianbiao/notify-services') as Promise<NotifyService[]>

/** 阈值告警规则列表(可按电表过滤) */
export const getAlerts = (meterId?: string) =>
  window.$request.get('/dianbiao/alerts', { params: meterId ? { meter_id: meterId } : {} }) as Promise<MeterAlert[]>

/** 新增阈值告警规则 */
export const createAlert = (data: {
  meter_id: string; metric: string; condition: 'lt' | 'gt'; threshold: number
  service_id: number; cooldown_minutes: number; enabled: number
}) => window.$request.post('/dianbiao/thresholds', data) as Promise<{ id: number }>

/** 更新阈值告警规则 */
export const updateAlert = (id: number, data: Partial<{
  metric: string; condition: 'lt' | 'gt'; threshold: number; service_id: number
  cooldown_minutes: number; enabled: number
}>) => window.$request.put(`/dianbiao/thresholds/${id}`, data) as Promise<{ id: number }>

/** 删除阈值告警规则 */
export const deleteAlert = (id: number) =>
  window.$request.delete(`/dianbiao/thresholds/${id}`) as Promise<{ id: number }>

// ---------- 充值记录(上报时自动识别) ----------

export interface ChargeRecord {
  id: number
  meter_id: string
  meter_name?: string
  ts: string
  prev_value: number | null   // 充值前剩余
  new_value: number | null    // 充值后剩余
  delta: number | null        // 增加量(优先订单金额)
  order_value?: number | null
  mode?: 'order' | 'jump'
  mode_label?: string
  amount_label?: string
  created_at?: string
}

/** 充值记录(时间倒序) */
export const getCharges = (meterId?: string, limit = 50) =>
  window.$request.get('/dianbiao/charges', {
    params: { ...(meterId ? { meter_id: meterId } : {}), limit }
  }) as Promise<ChargeRecord[]>