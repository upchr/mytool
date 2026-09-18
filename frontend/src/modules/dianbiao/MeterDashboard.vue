<template>
  <div class="dianbiao-dashboard">
    <n-card size="small" :bordered="false" class="toolbar-card">
      <n-space justify="space-between" align="center" wrap>
        <n-space align="center">
          <n-icon size="22" :component="FlashOutline" color="#18a058" />
          <span style="font-size: 16px; font-weight: 600">电表实时数据</span>
          <n-tag v-if="latest && latest.switch_status === 1" type="success" size="small">合闸</n-tag>
          <n-tag v-else-if="latest && latest.switch_status === 0" type="error" size="small">拉闸</n-tag>
          <n-tag v-else size="small" type="default">状态未知</n-tag>
        </n-space>
        <n-space align="center">
          <n-select
            v-model:value="meterId"
            :options="meterOptions"
            placeholder="选择电表"
            style="width: 260px"
            @update:value="switchMeter"
          />
          <n-select
            v-model:value="rangeHours"
            :options="rangeOptions"
            style="width: 110px"
            @update:value="loadAll"
          />
          <n-button :loading="loading" @click="loadAll">
            <template #icon><n-icon><refresh-outline /></n-icon></template>
            刷新
          </n-button>
          <n-button quaternary type="primary" @click="openTokenPanel">
            <template #icon><n-icon><key-outline /></n-icon></template>
            推送Token
          </n-button>
          <n-button quaternary @click="openCfgPanel">
            <template #icon><n-icon><options-outline /></n-icon></template>
            采集配置
          </n-button>
          <n-button quaternary type="warning" @click="openAlertPanel">
            <template #icon><n-icon><notifications-outline /></n-icon></template>
            阈值告警
          </n-button>
          <n-button quaternary tag="a" href="https://gitee.com/upchr/baozupo" target="_blank">
            <template #icon><n-icon><git-branch-outline /></n-icon></template>
            电表项目源码
          </n-button>
        </n-space>
      </n-space>
      <div v-if="lastTs" class="last-ts">最近采样: {{ lastTs }}</div>
    </n-card>

    <n-spin :show="loading">
      <n-grid cols="2 s:3 m:4 l:8" responsive="screen" :x-gap="12" :y-gap="12">
        <n-grid-item v-for="card in statCards" :key="card.label">
          <n-card size="small" class="stat-card" :bordered="true">
            <div class="stat-label">
              <n-icon :component="card.icon" :color="card.color" size="18" />
              <span style="margin-left: 6px">{{ card.label }}</span>
            </div>
            <div class="stat-value" :style="{ color: card.color }">
              {{ card.value }}<span class="stat-unit">{{ card.unit }}</span>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid cols="1 m:2" responsive="screen" :x-gap="12" :y-gap="12" style="margin-top: 12px">
        <n-grid-item>
          <n-card size="small" title="剩余电量 / 累计用量趋势">
            <div ref="surplusChartRef" class="chart-box" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small" title="功率曲线 (W)">
            <div ref="powerChartRef" class="chart-box" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small" title="电压 / 电流">
            <div ref="viChartRef" class="chart-box" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small">
            <template #header>
              <n-space align="center" justify="space-between" style="width: 100%">
                <span>用电量 (度)</span>
                <n-radio-group v-model:value="dailyBucket" size="small" @update:value="loadDailyStats">
                  <n-radio-button value="day">日 · 本周每日</n-radio-button>
                  <n-radio-button value="month">月 · 当年每月</n-radio-button>
                  <n-radio-button value="year">年 · 历年</n-radio-button>
                </n-radio-group>
              </n-space>
            </template>
            <div ref="dailyChartRef" class="chart-box" />
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-card size="small" style="margin-top: 12px">
        <template #header>
          <n-tabs v-model:value="detailTab" size="small" type="segment" @update:value="onDetailTabChange">
            <n-tab-pane name="samples" tab="最近采样明细" />
            <n-tab-pane name="charges" tab="充值记录" />
          </n-tabs>
        </template>
        <n-data-table v-if="detailTab === 'samples'" :columns="columns" :data="readings"
                      size="small" :max-height="360" />
        <div v-else>
          <div style="margin-bottom: 6px; color: #909399; font-size: 12px">
            识别规则: 剩余电量环比上涨大于 5 度, 或报文 order_value 增量; 充值金额按 {{ KWH_PRICE }} 元/度 折算后展示(order 模式按报文原值)
          </div>
          <n-data-table :columns="chargeColumns" :data="charges"
                        size="small" :max-height="330" :loading="loadingCharges" />
        </div>
      </n-card>
    </n-spin>

    <!-- 推送 Token 管理 -->
    <n-modal
      v-model:show="showTokenPanel"
      preset="card"
      title="推送 Token 维护"
      style="width: 720px"
      :mask-closable="false"
    >
      <n-alert type="info" :bordered="false" style="margin-bottom: 12px">
        采集器通过 <code>X-Agent-Token</code> 推数上传。在此创建/作废 Token,将 Token 填入采集器
        <code>.env</code> 的 <code>MYTOOL_AGENT_TOKEN</code> 即可使用;作废后采集端立即失效。
      </n-alert>

      <n-space style="margin-bottom: 12px">
        <n-input v-model:value="newTokenName" placeholder="用途备注, 如: 客厅电表采集器" style="width: 300px" />
        <n-button type="primary" :loading="creatingToken" @click="handleCreateToken">
          <template #icon><n-icon><add-circle-outline /></n-icon></template>
          创建 Token
        </n-button>
      </n-space>

      <n-data-table
        :columns="tokenColumns"
        :data="tokens"
        size="small"
        :max-height="340"
        :loading="loadingTokens"
      />
    </n-modal>

    <!-- 采集配置: 采集器下发 + 采集触发器(节点/目录) -->
    <n-modal
      v-model:show="showCfgPanel"
      preset="card"
      title="采集配置"
      style="width: 860px"
      :mask-closable="false"
    >
      <n-tabs type="line">
        <n-tab-pane name="collector" tab="采集器配置">
          <n-alert type="info" :bordered="false" style="margin-bottom: 12px">
            配置由 mytool 反向下发给采集器, 保存即时生效; 间隔建议 ≥60 秒。
            「启停」开关会<b>同步到节点进程</b>: 开 = 拉起并恢复采集, 关 = 停止采集(后台待命)。
            本页与「采集触发器」页操作的是同一个状态, 在哪一页开/关效果一致。
          </n-alert>
          <n-data-table
            :columns="cfgColumns"
            :data="cfgRows"
            size="small"
            :max-height="360"
            :loading="loadingCfg"
          />
        </n-tab-pane>

        <n-tab-pane name="trigger" tab="采集触发器">
<n-alert type="info" :bordered="false" style="margin-bottom: 12px">
            在目标节点(节点管理中维护 SSH 凭据)的工程目录上搭建采集触发器:
            <code>初始化</code> 会先把「代码源目录」打包(自动排除 <code>.env</code> 等敏感文件)
            经 SFTP 分发到节点, 再执行 <code>python meter_read.py --doctor</code> 环境自检,
            通过后自动读取采集器 SN 并反推基线配置; 保存(启停/间隔)即时下发, 采集器下一轮自动生效。
            <code>mytool地址</code> 留空自动推断(环境变量/本机 IP+8000), 也可自定义填写;
            <b>运行开关=运行</b> 时初始化结束会自动在节点拉起采集进程, 停采则不拉起。
          </n-alert>
          <n-space align="center" style="margin-bottom: 12px" wrap>
            <n-select v-model:value="trigNodeId" :options="nodeOptions" placeholder="所属节点" clearable style="width: 140px" />
            <n-input v-model:value="trigWorkDir" placeholder="采集器目录, 如 /opt/dianbiao" style="width: 160px" />
            <n-input v-model:value="trigMeterId" placeholder="SN" style="width: 150px" clearable />
            <n-input v-model:value="trigMac" placeholder="MAC" style="width: 150px" clearable />
            <n-input v-model:value="trigToken" placeholder="上报Token(留空自动创建)" style="width: 150px" clearable />
            <n-input v-model:value="trigMytoolUrl" placeholder="mytool地址(留空自动)" style="width: 150px" clearable />
            <n-input v-model:value="trigSourceDir" placeholder="代码源目录" style="width: 130px" clearable />
            <n-input-number v-model:value="trigInterval" :min="30" :max="86400" :step="30" style="width: 100px" placeholder="间隔秒" />
            <n-switch v-model:value="trigEnabled" size="small">
              <template #checked>运行</template>
              <template #unchecked>停采</template>
            </n-switch>
            <n-button type="primary" :loading="creatingTrig" @click="handleCreateTrigger">
              <template #icon><n-icon><add-circle-outline /></n-icon></template>
              搭建触发器
            </n-button>
          </n-space>
          <n-data-table
            :columns="trigColumns"
            :data="trigRows"
            size="small"
            :max-height="320"
            :scroll-x="1560"
            :loading="loadingTrig"
          />
        </n-tab-pane>
      </n-tabs>
    </n-modal>

    <!-- 阈值告警: 读数上报时评估, 命中后经「通知渠道」页已启用渠道推送 -->
    <n-modal
      v-model:show="showAlertPanel"
      preset="card"
      title="阈值告警"
      style="width: 960px"
      :mask-closable="false"
    >
      <n-alert type="info" :bordered="false" style="margin-bottom: 12px">
        收到新的抄表数据时自动评估规则, 命中后经下方所选通知渠道推送(为避免刷屏, 按冷却时间节流)。
        渠道取自「通知渠道」页<b>已启用</b>的配置;
        <span v-if="!notifyServices.length" style="color:#d03050">当前没有已启用的渠道, 请先到「通知渠道」页启用一个。</span>
      </n-alert>

      <n-space align="center" style="margin-bottom: 12px" wrap>
        <n-select v-model:value="newAlert.metric" :options="metricOptions" style="width: 130px" />
        <n-select v-model:value="newAlert.condition" :options="conditionOptions" style="width: 90px" />
        <n-input-number v-model:value="newAlert.threshold" :min="0" :step="1" :placeholder="`阈值(${alertUnit})`"
                        style="width: 110px" :show-button="false" />
        <n-select v-model:value="newAlert.service_id" :options="notifyServices" style="width: 150px"
                  placeholder="通知渠道" />
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-input-number v-model:value="newAlert.cooldown_minutes" :min="1" :max="1440" style="width: 130px"
                            :show-button="false" placeholder="冷却分钟" />
          </template>
          命中后多少分钟内不重复告警
        </n-tooltip>
        <n-button type="primary" :loading="creatingAlert" @click="handleAddAlert">
          <template #icon><n-icon><add-circle-outline /></n-icon></template>
          新增规则
        </n-button>
      </n-space>

      <n-data-table
        :columns="alertColumns"
        :data="alerts"
        size="small"
        :max-height="340"
        :loading="loadingAlerts"
      />
    </n-modal>

    <!-- 触发器初始化输出 -->
    <n-modal v-model:show="showTrigOutput" preset="card" title="初始化输出 (doctor)" style="width: 720px">
      <pre style="white-space: pre-wrap; background: #f5f7fa; border-radius: 6px; padding: 12px; max-height: 420px; overflow: auto; font-size: 12px">{{ trigOutput }}</pre>
    </n-modal>

    <!-- 采集日志(节点侧 SSH tail) -->
    <n-modal v-model:show="showTrigLog" preset="card" title="采集日志 (节点 collector.log)" style="width: 860px" :mask-closable="false">
      <template #header>
        <n-space align="center">
          <span>采集日志</span>
          <n-tag size="small" type="info">最近 {{ trigLogLines }} 行</n-tag>
        </n-space>
      </template>
      <div style="color:#909399;font-size:12px;margin-bottom:8px">
        触发器已安装自愈保活: 节点每 5 分钟自检一次, 后端 enabled=1 且采集器进程不在时自动拉起; 面板暂停(enabled=0)期间保持待命不干扰。
      </div>
      <n-spin :show="loadingTrigLog">
        <pre style="white-space: pre-wrap; background: #f5f7fa; border-radius: 6px; padding: 12px; max-height: 480px; overflow: auto; font-size: 12px">{{ trigLog }}</pre>
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, h } from 'vue'
import * as echarts from 'echarts'
import {
  FlashOutline, SpeedometerOutline, PulseOutline, BatteryHalfOutline,
  ThermometerOutline, PowerOutline, StatsChartOutline, RefreshOutline,
  SwapHorizontalOutline, KeyOutline, AddCircleOutline, GitBranchOutline,
  OptionsOutline, CalendarOutline, CalendarClearOutline, CalendarNumberOutline, TimeOutline,
  NotificationsOutline,
} from '@vicons/ionicons5'
import * as dianbiaoApi from '@/api/dianbiao'

const meterId = ref('')
const meterOptions = ref([])
const rangeHours = ref(24)
const rangeOptions = [
  { label: '1小时', value: 1 },
  { label: '6小时', value: 6 },
  { label: '24小时', value: 24 },
  { label: '7天', value: 168 },
]
const loading = ref(false)
const lastTs = ref(null)
const readings = ref([])
const latest = ref(null)
const dailyStats = ref([])
const usageSummary = ref({ day: null, week: null, month: null, year: null })

const surplusChartRef = ref(null)
const powerChartRef = ref(null)
const viChartRef = ref(null)
const dailyChartRef = ref(null)
const charts = {}
let resizeObserver = null
let refreshTimer = null

// ---------- Token 维护 ----------
const showTokenPanel = ref(false)
const tokens = ref([])
const loadingTokens = ref(false)
const creatingToken = ref(false)
const newTokenName = ref('')

// ---------- 用电量聚合粒度(日=本周每日 / 月=当年每月 / 年=历年) ----------
const dailyBucket = ref('day')
const DAILY_LABELS = { day: '本周', month: '当月', year: '历年' }

// ---------- 采集器运行配置(mytool 反向下发) ----------
const showCfgPanel = ref(false)
const cfgRows = ref([])
const loadingCfg = ref(false)

// ---------- 最近采样明细 / 充值记录 双表 ----------
const detailTab = ref('samples')
const charges = ref([])
const loadingCharges = ref(false)

// ---------- 采集触发器(节点 + 目录 + 初始化/启停) ----------
const trigRows = ref([])
const loadingTrig = ref(false)
const creatingTrig = ref(false)
const initTrigId = ref(null)
const nodeOptions = ref([])
const trigNodeId = ref(null)
const trigWorkDir = ref('')
const trigMeterId = ref('')
const trigMac = ref('')
const trigToken = ref('')
const trigMytoolUrl = ref('')
const trigSourceDir = ref('')
const trigInterval = ref(300)
const trigEnabled = ref(true)
const showTrigOutput = ref(false)
const trigOutput = ref('')
const showTrigLog = ref(false)
const trigLog = ref('')
const trigLogLines = ref(300)
const loadingTrigLog = ref(false)

// ---------- 阈值告警(复用「通知渠道」页已启用渠道) ----------
const showAlertPanel = ref(false)
const alerts = ref([])
const loadingAlerts = ref(false)
const creatingAlert = ref(false)
const notifyServices = ref([])
const metricOptions = [
  { label: '剩余电量(度)', value: 'surplus_value' },
  { label: '累计用电(度)', value: 'total_value' },
  { label: '功率(W)', value: 'power' },
  { label: '电压(V)', value: 'voltage' },
  { label: '电流(A)', value: 'current' },
]
const conditionOptions = [
  { label: '低于', value: 'lt' },
  { label: '高于', value: 'gt' },
]
const newAlert = ref({ metric: 'surplus_value', condition: 'lt', threshold: null, service_id: null, cooldown_minutes: 10 })
const METRIC_UNITS = { surplus_value: '度', total_value: '度', power: 'W', voltage: 'V', current: 'A' }
const alertUnit = computed(() => METRIC_UNITS[newAlert.value.metric] || '')

async function loadNodeOptions() {
  try {
    const nodes = await window.$request.get('/nodes/only_active/true')
    nodeOptions.value = nodes.map((n) => ({
      label: `${n.name} (${n.host})`,
      value: n.id,
    }))
  } catch (e) { console.error('加载节点失败:', e) }
}

const trigColumns = [
  { title: '触发器', key: 'name', width: 130, ellipsis: { tooltip: true } },
  {
    title: '所属节点', key: 'node_name', width: 130,
    render: (r) => h('span', {}, `${r.node_name || '?'} ·${r.node_host || ''}`),
  },
  { title: '采集目录', key: 'work_dir', width: 140, ellipsis: { tooltip: true } },
  { title: '代码源目录', key: 'source_dir', width: 130, ellipsis: { tooltip: true }, render: (r) => r.source_dir || '—' },
  {
    title: 'SN', key: 'meter_id', width: 126,
    render: (r) => h('input', {
      type: 'text', value: r.meter_id || '', placeholder: '识别',
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.meter_id = e.target.value.trim() || null },
    }),
  },
  {
    title: 'MAC', key: 'ym_mac', width: 138,
    render: (r) => h('input', {
      type: 'text', value: r.ym_mac || '',
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.ym_mac = e.target.value.trim() || null },
    }),
  },
  {
    title: '上报Token', key: 'agent_token', width: 126, ellipsis: { tooltip: true },
    render: (r) => h('input', {
      type: 'text', value: r.agent_token || '', placeholder: '自动创建',
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.agent_token = e.target.value.trim() || null },
    }),
  },
  {
    title: 'mytool地址', key: 'mytool_url', width: 130, ellipsis: { tooltip: true },
    render: (r) => h('input', {
      type: 'text', value: r.mytool_url || '', placeholder: '自动推断',
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.mytool_url = e.target.value.trim() || null },
    }),
  },
  {
    title: '采集间隔(秒)', key: 'interval_seconds', width: 110,
    render: (r) => h('input', {
      type: 'number', min: 30, max: 86400, step: 30, value: r.interval_seconds,
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.interval = Number(e.target.value) || 300 },
    }),
  },
  {
    title: '启停', key: 'enabled', width: 80,
    render: (r) => {
      const on = (r.enabled === 1)
      return h('span', {
        style: `cursor:pointer;color:${on ? '#18a058' : '#d03050'};font-weight:600`,
        onClick: () => { r.enabled = on ? 0 : 1 },
      }, on ? '● 运行' : '○ 停采')
    },
  },
  {
    title: '最近上报', key: 'last_seen', width: 150,
    render: (r) => h('span', { style: r.last_seen ? '' : 'color:#c0c4cc' }, fmtTs(r.last_seen)),
  },
  {
    title: '初始化', key: 'init_status', width: 90,
    render: (r) => {
      const st = r.init_status || 'pending'
      const color = st === 'ok' ? '#18a058' : st === 'fail' ? '#d03050' : '#909399'
      const label = st === 'ok' ? '正常' : st === 'fail' ? '失败' : '未初始化'
      return h('a', {
        style: `cursor:pointer;color:${color};font-weight:600`,
        title: (r.init_output || '').slice(0, 200),
        onClick: () => { trigOutput.value = r.init_output || '(无输出)'; showTrigOutput.value = true },
      }, label)
    },
  },
  {
    title: '操作', key: 'ops', width: 200,
    render: (r) => {
      const btns = [
        h('a', {
          style: 'cursor:pointer;color:#2080f0;margin-right:10px',
          onClick: () => initTrigRow(r),
        }, initTrigId.value === r.id ? '初始中…' : '初始化'),
        h('a', {
          style: 'cursor:pointer;color:#18a058;margin-right:10px',
          onClick: () => saveTrigRow(r),
        }, '保存下发'),
        h('a', {
          style: 'cursor:pointer;color:#909399;margin-right:10px',
          onClick: () => openTrigLog(r),
        }, '日志'),
        h('a', {
          style: 'cursor:pointer;color:#d03050',
          onClick: () => removeTrigRow(r),
        }, '删除'),
      ]
      return h('span', {}, btns)
    },
  },
]

const alertColumns = [
  { title: '指标', key: 'metric', width: 100, render: (r) => h('span', {}, r.metric_label || r.metric) },
  { title: '条件', key: 'condition', width: 70, render: (r) => h('span', {}, r.condition_label || r.condition) },
  {
    title: '阈值', key: 'threshold', width: 110,
    render: (r) => h('span', {}, `${r.threshold}${r.unit || ''}`),
  },
  {
    title: '通知渠道', key: 'service_name', width: 130, ellipsis: { tooltip: true },
    render: (r) => h('span', {}, r.service_name || `渠道#${r.service_id}(已停用)`),
  },
  { title: '冷却(分)', key: 'cooldown_minutes', width: 90 },
  {
    title: '最近触发', key: 'last_alert_at', width: 150,
    render: (r) => {
      if (!r.last_alert_at) return h('span', { style: 'color:#909399' }, '未触发')
      const t = new Date(r.last_alert_at)
      const pad = (n) => String(n).padStart(2, '0')
      return h('span', {}, `${pad(t.getMonth() + 1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}${r.last_value != null ? ` (${r.last_value}${r.unit || ''})` : ''}`)
    },
  },
  {
    title: '启用', key: 'enabled', width: 80,
    render: (r) => {
      const on = (r.enabled === 1)
      return h('span', {
        style: `cursor:pointer;color:${on ? '#18a058' : '#909399'};font-weight:600`,
        onClick: () => toggleAlert(r),
      }, on ? '● 启用' : '○ 停用')
    },
  },
  {
    title: '操作', key: 'ops', width: 60,
    render: (r) => h('a', {
      style: 'cursor:pointer;color:#d03050',
      onClick: () => removeAlert(r),
    }, '删除'),
  },
]

async function openAlertPanel() {
  showAlertPanel.value = true
  await Promise.all([loadAlerts(), loadNotifyServices()])
}

async function loadNotifyServices() {
  try {
    const list = await dianbiaoApi.getNotifyServices()
    notifyServices.value = list.map((s) => ({
      label: `${s.service_name} (${s.service_type})`,
      value: s.id,
    }))
  } catch (e) { console.error('加载通知渠道失败:', e) }
}

async function loadAlerts() {
  loadingAlerts.value = true
  try {
    alerts.value = await dianbiaoApi.getAlerts(meterId.value || undefined)
  } catch (e) { console.error(e) } finally {
    loadingAlerts.value = false
  }
}

async function handleAddAlert() {
  if (!meterId.value) { window.$message.warning('请先在上方选择电表'); return }
  if (newAlert.value.threshold == null) { window.$message.warning('请填写阈值'); return }
  if (!newAlert.value.service_id) { window.$message.warning('请选择通知渠道'); return }
  creatingAlert.value = true
  try {
    await dianbiaoApi.createAlert({
      meter_id: meterId.value,
      metric: newAlert.value.metric,
      condition: newAlert.value.condition,
      threshold: Number(newAlert.value.threshold),
      service_id: newAlert.value.service_id,
      cooldown_minutes: Number(newAlert.value.cooldown_minutes) || 10,
      enabled: 1,
    })
    window.$message.success('规则已添加, 下次上报命中即触发')
    newAlert.value = { metric: 'surplus_value', condition: 'lt', threshold: null, service_id: null, cooldown_minutes: 10 }
    await loadAlerts()
  } catch (e) { console.error(e) } finally {
    creatingAlert.value = false
  }
}

async function toggleAlert(r) {
  try {
    await dianbiaoApi.updateAlert(r.id, { enabled: r.enabled === 1 ? 0 : 1 })
    r.enabled = r.enabled === 1 ? 0 : 1
    window.$message.success(r.enabled === 1 ? '规则已启用' : '规则已停用')
  } catch (e) { console.error(e) }
}

async function removeAlert(r) {
  window.$dialog.warning({
    title: '删除规则',
    content: `确定删除「${r.metric_label || r.metric} ${r.condition_label || r.condition} ${r.threshold}${r.unit || ''}」规则?`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await dianbiaoApi.deleteAlert(r.id)
        window.$message.success('已删除')
        await loadAlerts()
      } catch (e) { console.error(e) }
    },
  })
}

async function openCfgPanel() {
  showCfgPanel.value = true
  if (!nodeOptions.value.length) await loadNodeOptions()
  await Promise.all([loadCfgRows(), loadTrigRows()])
}

async function loadTrigRows() {
  loadingTrig.value = true
  try {
    trigRows.value = await dianbiaoApi.getTriggeres()
    trigRows.value.forEach((r) => { r.interval = r.interval_seconds })
  } catch (e) { console.error(e) } finally {
    loadingTrig.value = false
  }
}

async function handleCreateTrigger() {
  if (!trigNodeId.value) { window.$message.warning('请选择所属节点'); return }
  if (!trigWorkDir.value.trim()) { window.$message.warning('请填写采集器目录'); return }
  creatingTrig.value = true
  try {
    await dianbiaoApi.createTrigger({
      node_id: trigNodeId.value,
      work_dir: trigWorkDir.value.trim(),
      source_dir: trigSourceDir.value.trim() || undefined,
      meter_id: trigMeterId.value.trim() || undefined,
      ym_mac: trigMac.value.trim() || undefined,
      agent_token: trigToken.value.trim() || undefined,
      mytool_url: trigMytoolUrl.value.trim() || undefined,
      interval_seconds: Number(trigInterval.value) || 300,
      enabled: trigEnabled.value ? 1 : 0,
    })
    window.$message.success('触发器已搭建, 点击「初始化」同步代码、下发配置并远端自检')
    trigWorkDir.value = ''
    trigMeterId.value = ''
    trigMac.value = ''
    trigToken.value = ''
    trigMytoolUrl.value = ''
    trigSourceDir.value = ''
    trigEnabled.value = true
    trigInterval.value = 300
    await loadTrigRows()
  } catch (e) { console.error(e) } finally {
    creatingTrig.value = false
  }
}

async function initTrigRow(row) {
  initTrigId.value = row.id
  try {
    const res = await dianbiaoApi.initTrigger(row.id)
    if (res.init_status === 'ok') {
      window.$message.success(res.meter_id
        ? `自检通过, 已识别采集器 ${res.meter_id} 并反推基线配置`
        : '自检通过(未识别到采集器 SN, 检查 .env 的 YM_SN)')
    } else {
      window.$message.error('自检失败, 点击状态列查看 doctor 输出')
    }
    trigOutput.value = res.output || '(无输出)'
    showTrigOutput.value = true
    await Promise.all([loadTrigRows(), loadCfgRows()])
  } catch (e) { console.error(e) } finally {
    initTrigId.value = null
  }
}

async function saveTrigRow(row) {
  try {
    const res = await dianbiaoApi.updateTrigger(row.id, {
      meter_id: row.meter_id || undefined,
      ym_mac: row.ym_mac || undefined,
      agent_token: row.agent_token || undefined,
      mytool_url: row.mytool_url || undefined,
      interval_seconds: Number(row.interval) || 300,
      enabled: row.enabled === 1 ? 1 : 0,
    })
    window.$message.success(res.pushed
      ? ('配置已下发, 节点采集器下一轮自动生效' + (res.proc ? ` (${res.proc})` : '') + (res.keepalive ? `; ${res.keepalive}` : ''))
      : ('已保存(初始化后自动反推配置)' + (res.keepalive ? `; ${res.keepalive}` : '')))
    await loadTrigRows()
  } catch (e) { console.error(e) }
}

/** 查看节点侧采集日志(SSH tail collector.log) */
async function openTrigLog(row) {
  loadingTrigLog.value = true
  try {
    const res = await dianbiaoApi.getTriggerLogs(row.id, 300)
    trigLogLines.value = res.lines || 300
    trigLog.value = res.logs || '(空日志)'
    showTrigLog.value = true
  } catch (e) {
    console.error(e)
    window.$message.error('读取节点日志失败: ' + (e?.message || e))
  } finally {
    loadingTrigLog.value = false
  }
}

async function removeTrigRow(row) {
  try {
    await dianbiaoApi.deleteTrigger(row.id)
    window.$message.success('触发器已删除')
    await loadTrigRows()
  } catch (e) { console.error(e) }
}

const fmtTs = (v) => (v ? String(v).replace('T', ' ').slice(0, 19) : '-')

async function copyToken(token) {
  try {
    await navigator.clipboard.writeText(token)
    window.$message.success('Token 已复制到剪贴板')
  } catch (e) {
    window.$copyCode && window.$copyCode(token)
  }
}

// ---------- 充值记录(上报时自动识别) ----------
const KWH_PRICE = 1.3 // 电费单价(元/度), 仅用于换算「充值金额」展示; 表内数值一律以度为准
const chargeColumns = [
  { title: '时间', key: 'ts', width: 150, render: (r) => fmtTs(r.ts) },
  {
    title: '充值前(度)', key: 'prev_value', width: 100,
    render: (r) => (r.prev_value == null ? '-' : fmt(r.prev_value)),
  },
  {
    title: '充值后(度)', key: 'new_value', width: 100,
    render: (r) => (r.new_value == null ? '-' : fmt(r.new_value)),
  },
  {
    title: '增加(度)', key: 'delta', width: 100,
    render: (r) => {
      if (r.delta == null) return '-'
      return h('span', { style: 'color:#18a058;font-weight:600' }, `+${fmt(r.delta)}`)
    },
  },
  {
    title: '充值金额(元)', key: 'amount', width: 110,
    render: (r) => {
      if (r.delta == null) return '-'
      // jump=剩余度增量×单价; order=报文原值增量(本身即金额)
      const amt = r.mode === 'order' ? r.delta : r.delta * KWH_PRICE
      return h('span', { style: 'color:#18a058;font-weight:600' }, `¥${fmt(amt)}`)
    },
  },
  {
    title: '识别来源', key: 'mode', width: 110,
    render: (r) => {
      const isOrder = r.mode === 'order'
      return h('span', {
        style: `color:${isOrder ? '#2080f0' : '#f0a020'};font-weight:600`,
      }, isOrder ? '订单金额' : '剩余跳变')
    },
  },
]

async function loadCharges() {
  if (!meterId.value) return
  loadingCharges.value = true
  try {
    charges.value = await dianbiaoApi.getCharges(meterId.value, 50)
  } catch (e) { console.error('加载充值记录失败:', e) } finally {
    loadingCharges.value = false
  }
}

function onDetailTabChange(tab) {
  if (tab === 'charges' && !charges.value.length) loadCharges()
}

const tokenColumns = [
  { title: 'ID', key: 'id', width: 50 },
  { title: '用途', key: 'name', width: 140 },
  {
    title: 'Token', key: 'token', ellipsis: { tooltip: true }, render: (r) => h('code', {}, r.token),
  },
  {
    title: '状态', key: 'status', width: 80,
    render: (r) => h('span', { style: { color: r.status === 'active' ? '#18a058' : '#d03050' } },
      r.status === 'active' ? '启用' : '已作废'),
  },
  { title: '上次使用', key: 'last_used_at', width: 150, render: (r) => fmtTs(r.last_used_at) },
  { title: '创建时间', key: 'created_at', width: 150, render: (r) => fmtTs(r.created_at) },
  {
    title: '操作', key: 'ops', width: 130,
    render: (row) => {
      if (row.status !== 'active') return null
      return [
        h('a', { style: 'cursor:pointer; margin-right:10px', onClick: () => copyToken(row.token) }, '复制'),
        h('a', { style: 'cursor:pointer; color:#d03050', onClick: () => handleRevokeToken(row) }, '作废'),
      ]
    },
  },
]

async function openTokenPanel() {
  showTokenPanel.value = true
  await loadTokens()
}

async function loadTokens() {
  loadingTokens.value = true
  try {
    tokens.value = await dianbiaoApi.getTokens()
  } catch (e) { console.error(e) } finally {
    loadingTokens.value = false
  }
}

async function handleCreateToken() {
  const name = newTokenName.value.trim()
  if (!name) {
    window.$message.warning('请填写用途备注')
    return
  }
  creatingToken.value = true
  try {
    const t = await dianbiaoApi.createToken(name)
    tokens.value.unshift(t)
    newTokenName.value = ''
    copyToken(t.token)
    window.$message.success(`已创建并复制 Token(备注: ${t.name})`)
  } catch (e) { console.error(e) } finally {
    creatingToken.value = false
  }
}

async function handleRevokeToken(row) {
  try {
    await dianbiaoApi.revokeToken(row.id)
    row.status = 'revoked'
    row.revoked_at = new Date().toISOString()
    window.$message.success(`Token #${row.id} 已作废, 采集端立即失效`)
  } catch (e) { console.error(e) }
}

// ---------- 采集器运行配置 ----------

const cfgColumns = [
  {
    title: '采集器', key: 'meter_id', width: 220,
    render: (r) => h('div', {}, [
      h('div', { style: 'font-weight:600' }, r.name || r.meter_id),
      h('div', { style: 'font-size:12px;color:#909399' },
        `${r.meter_id} ${r.configured ? '· 最近更新 ' + fmtTs(r.updated_at) : '· 未下发(用默认值)'}`),
    ]),
  },
  {
    title: '最近上报', key: 'last_seen', width: 160,
    render: (r) => fmtTs(r.last_seen),
  },
  {
    title: '采集间隔(秒)', key: 'interval_seconds', width: 160,
    render: (r) => h('input', {
      type: 'number', min: 30, max: 86400, step: 30, value: r.interval_seconds,
      style: 'width:100%;padding:4px 8px;border:1px solid #ddd;border-radius:4px',
      onInput: (e) => { r.interval = Number(e.target.value) || 300 },
    }),
  },
  {
    title: '启停', key: 'enabled', width: 90,
    render: (r) => {
      const on = (r.enabled === 1)
      return h('span', {
        style: `cursor:pointer;color:${on ? '#18a058' : '#d03050'};font-weight:600`,
        onClick: () => toggleCfgEnabled(r),
      }, on ? '● 采集中' : '○ 已暂停')
    },
  },
  {
    title: '操作', key: 'ops', width: 90,
    render: (r) => h('a', {
      style: 'cursor:pointer;color:#2080f0',
      onClick: () => saveCfgRow(r),
    }, '保存下发'),
  },
]

async function loadCfgRows() {
  loadingCfg.value = true
  try {
    cfgRows.value = await dianbiaoApi.getCollectorConfigs()
    cfgRows.value.forEach((r) => { r.interval = r.interval_seconds })
  } catch (e) { console.error(e) } finally {
    loadingCfg.value = false
  }
}

/** 启停切换: 二次确认后保存, 后端会同步到节点采集进程(与触发器页行为一致) */
function toggleCfgEnabled(r) {
  const on = (r.enabled === 1)
  window.$dialog.warning({
    title: on ? '确认暂停采集？' : '确认恢复采集？',
    content: `「${r.name || r.meter_id}」将${on ? '暂停' : '恢复'}采集, 立即保存并同步节点进程, 不用再管其他页面。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      r.enabled = on ? 0 : 1
      await saveCfgRow(r)
    },
  })
}

async function saveCfgRow(row) {
  try {
    const res = await dianbiaoApi.saveCollectorConfig({
      meter_id: row.meter_id,
      interval_seconds: Number(row.interval) || 300,
      enabled: row.enabled === 1 ? 1 : 0,
    })
    window.$message.success(`${row.name || row.meter_id} 配置已保存` + (res?.proc ? ` · ${res.proc}` : ''))
    await loadCfgRows()
  } catch (e) { console.error(e) }
}

const fmt = (v, digits = 2) =>
  v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(digits)

const statCards = computed(() => {
  const l = latest.value || {}
  const u = usageSummary.value || {}
  return [
    { label: '今日用电', value: fmt(u.day), unit: '度', color: '#f0a020', icon: CalendarOutline },
    { label: '本周用电', value: fmt(u.week), unit: '度', color: '#2080f0', icon: CalendarClearOutline },
    { label: '本月用电', value: fmt(u.month), unit: '度', color: '#18a058', icon: CalendarNumberOutline },
    { label: '本年用电', value: fmt(u.year), unit: '度', color: '#e88080', icon: TimeOutline },
    { label: '剩余电量', value: fmt(l.surplus_value), unit: '度', color: '#18a058', icon: BatteryHalfOutline },
    { label: '累计用量', value: fmt(l.total_value), unit: '度', color: '#2080f0', icon: SpeedometerOutline },
    { label: '当前功率', value: fmt(l.power, 0), unit: 'W', color: '#f0a020', icon: PowerOutline },
    { label: '电压', value: fmt(l.voltage, 1), unit: 'V', color: '#e88080', icon: FlashOutline },
    { label: '电流', value: fmt(l.current), unit: 'A', color: '#7f6bff', icon: ThermometerOutline },
    { label: '功率因数', value: fmt(l.pf), unit: '', color: '#63e2b7', icon: StatsChartOutline },
    { label: '开关状态', value: l.switch_status === 1 ? '合闸' : l.switch_status === 0 ? '拉闸' : '-', unit: '', color: l.switch_status === 1 ? '#18a058' : '#d03050', icon: SwapHorizontalOutline },
    { label: '采集点数', value: String(readings.value.length), unit: '条', color: '#909399', icon: StatsChartOutline },
  ]
})

const columns = [
  { title: '时间', key: 'ts', width: 200, render: (r) => fmtTs(r.ts) },
  { title: '剩余(度)', key: 'surplus_value', width: 110, render: (r) => fmt(r.surplus_value) },
  { title: '累计(度)', key: 'total_value', width: 110, render: (r) => fmt(r.total_value) },
  { title: '功率(W)', key: 'power', width: 100, render: (r) => fmt(r.power, 0) },
  { title: '电压(V)', key: 'voltage', width: 100, render: (r) => fmt(r.voltage, 1) },
  { title: '电流(A)', key: 'current', width: 100, render: (r) => fmt(r.current) },
  { title: '功率因数', key: 'pf', width: 100, render: (r) => (r.pf === null || r.pf === undefined ? '-' : (r.pf * 100).toFixed(1) + '%') },
  { title: '状态', key: 'status', width: 90, render: (r) => (r.status === 'ok' ? 'OK' : r.status) },
]

const initCharts = () => {
  if (!surplusChartRef.value) return
  const defs = [
    ['surplus', surplusChartRef.value],
    ['power', powerChartRef.value],
    ['vi', viChartRef.value],
    ['daily', dailyChartRef.value],
  ]
  for (const [name, el] of defs) {
    if (!el) continue
    if (charts[name]) charts[name].dispose()
    charts[name] = echarts.init(el)
  }
  resizeObserver = new ResizeObserver(() => {
    Object.values(charts).forEach((c) => c && c.resize())
  })
  resizeObserver.observe(surplusChartRef.value?.parentElement)
}

const tsLabels = (rows) => rows.map((r) => (r.ts ? r.ts.slice(5, 16).replace('T', ' ') : ''))

/** 当前图例显隐状态(供刷新后保持用户点选) */
const legendSelected = (ch, names) => {
  const opt = ch && ch.getOption ? ch.getOption() : null
  const saved = opt?.legend?.[0]?.selected || {}
  const out = {}
  names.forEach((n) => { out[n] = saved[n] ?? true })
  return out
}

const updateSurplusChart = (rows) => {
  const ch = charts.surplus
  if (!ch) return
  const labels = tsLabels(rows)
  const names = ['剩余电量', '累计用电']
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: names, top: 0, selected: legendSelected(charts.surplus, names) },
    grid: { left: 55, right: 55, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: labels },
    yAxis: [
      { type: 'value', name: '剩余(度)', scale: true },
      { type: 'value', name: '累计(度)', scale: true },
    ],
    series: [
      { name: '剩余电量', type: 'line', smooth: true, yAxisIndex: 0, data: rows.map((r) => r.surplus_value), areaStyle: { opacity: 0.15 }, itemStyle: { color: '#18a058' }, lineStyle: { color: '#18a058' } },
      { name: '累计用电', type: 'line', smooth: true, yAxisIndex: 1, data: rows.map((r) => r.total_value), itemStyle: { color: '#2080f0' }, lineStyle: { color: '#2080f0' } },
    ],
  }, true)
}

const updatePowerChart = (rows) => {
  const ch = charts.power
  if (!ch) return
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 55, right: 20, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: tsLabels(rows) },
    yAxis: { type: 'value', name: 'W' },
    series: [{ name: '功率', type: 'line', smooth: true, data: rows.map((r) => r.power), areaStyle: { opacity: 0.2 }, itemStyle: { color: '#f0a020' } }],
  }, true)
}

const updateViChart = (rows) => {
  const ch = charts.vi
  if (!ch) return
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 55, right: 55, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: tsLabels(rows) },
    yAxis: [
      { type: 'value', name: 'V' },
      { type: 'value', name: 'A' },
    ],
    series: [
      { name: '电压', type: 'line', smooth: true, data: rows.map((r) => r.voltage), itemStyle: { color: '#e88080' } },
      { name: '电流', type: 'line', smooth: true, yAxisIndex: 1, data: rows.map((r) => r.current), itemStyle: { color: '#7f6bff' } },
    ],
  }, true)
}

const updateDailyChart = () => {
  const ch = charts.daily
  if (!ch) return
  const days = dailyStats.value || []
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 55, right: 20, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: days.map((d) => d.label || d.bucket || d.day) },
    yAxis: { type: 'value', name: '度' },
    series: [
      {
        name: `用电量(${DAILY_LABELS[dailyBucket.value] || dailyBucket.value})`, type: 'bar',
        data: days.map((d) => d.usage),
        itemStyle: { color: '#2080f0' },
        markLine: {
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#f0a020', width: 1.5 },
          label: { formatter: '均值 {c}', color: '#f0a020', fontSize: 11, position: 'insideEndTop' },
          data: [{ type: 'average', name: '均值' }],
        },
      },
    ],
  }, true)
}

async function loadMeters() {
  const list = await dianbiaoApi.getMeters()
  meterOptions.value = list.map((m) => ({ label: m.name ? `${m.name} (${m.meter_id})` : m.meter_id, value: m.meter_id }))
  if (!meterId.value && list.length) meterId.value = list[0].meter_id
}

async function loadAll() {
  if (!meterId.value) return
  loading.value = true
  try {
    const [rows, latestRow] = await Promise.all([
      dianbiaoApi.getReadings(meterId.value, rangeHours.value),
      dianbiaoApi.getLatest(meterId.value),
    ])
    readings.value = rows
    latest.value = latestRow
    lastTs.value = latestRow?.ts ? String(latestRow.ts).replace('T', ' ').slice(0, 19) : null

    const sorted = [...rows].sort((a, b) => String(a.ts).localeCompare(String(b.ts)))
    updateSurplusChart(sorted)
    updatePowerChart(sorted)
    updateViChart(sorted)
    await Promise.all([loadDailyStats(), loadUsageCards()])
  } catch (e) {
    console.error('加载电表数据失败:', e)
  } finally {
    loading.value = false
  }
}

/** 用电量(度)卡片: 日=本周每日 / 月=当年每月 / 年=历年, 空桶补 0 */
async function loadDailyStats() {
  if (!meterId.value) return
  try {
    const mode = dailyBucket.value
    const now = new Date()
    const list = []
    if (mode === 'day') {
      // 当前自然周(周一起)逐日, 未来日子显示 0
      const monday = new Date(now)
      monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
      monday.setHours(0, 0, 0, 0)
      const start = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, '0')}-${String(monday.getDate()).padStart(2, '0')}`
      const res = await dianbiaoApi.getStats(meterId.value, 'day', undefined, start)
      const byDay = {}
      res.days.forEach((d) => { if (d.bucket) byDay[d.bucket] = d.usage })
      const weekNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      for (let i = 0; i < 7; i++) {
        const d = new Date(monday)
        d.setDate(d.getDate() + i)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        list.push({
          label: `${weekNames[i]} ${d.getMonth() + 1}/${String(d.getDate()).padStart(2, '0')}`,
          usage: d > now ? 0 : (byDay[key] ?? 0),
        })
      }
    } else if (mode === 'month') {
      // 当年 1~12 月, 未来月显示 0
      const year = now.getFullYear()
      const res = await dianbiaoApi.getStats(meterId.value, 'month', undefined, `${year}-01-01`)
      const byMonth = {}
      res.days.forEach((d) => { if (d.bucket) byMonth[d.bucket] = d.usage })
      for (let m = 1; m <= 12; m++) {
        const key = `${year}-${String(m).padStart(2, '0')}`
        const due = new Date(year, m - 1, 1)
        list.push({ label: `${m}月`, usage: due > now ? 0 : (byMonth[key] ?? 0) })
      }
    } else {
      // 历年(默认回溯窗口由后端按粒度决定)
      const res = await dianbiaoApi.getStats(meterId.value, 'year')
      res.days.forEach((d) => { list.push({ label: d.bucket, usage: d.usage ?? 0 }) })
    }
    dailyStats.value = list
    updateDailyChart()
  } catch (e) {
    console.error('加载用电量聚合失败:', e)
  }
}

/** 顶部门户卡: 日/周/月/年用电量(取对应粒度最后一个统计桶的增量) */
async function loadUsageCards() {
  if (!meterId.value) return
  try {
    const [day, week, month, year] = await Promise.all([
      dianbiaoApi.getStats(meterId.value, 'day', 2),
      dianbiaoApi.getStats(meterId.value, 'week', 8),
      dianbiaoApi.getStats(meterId.value, 'month', 32),
      dianbiaoApi.getStats(meterId.value, 'year', 366),
    ])
    const last = (s) => (s && s.days && s.days.length ? s.days[s.days.length - 1].usage : null)
    usageSummary.value = { day: last(day), week: last(week), month: last(month), year: last(year) }
  } catch (e) {
    console.error('加载门户用电量卡失败:', e)
  }
}

function switchMeter() {
  readings.value = []
  latest.value = null
  loadAll()
}

onMounted(async () => {
  initCharts()
  try { await loadMeters() } catch (e) { console.error(e) }
  await loadAll()
  refreshTimer = setInterval(() => loadAll(), 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (resizeObserver) resizeObserver.disconnect()
  Object.values(charts).forEach((c) => c && c.dispose())
})
</script>

<style scoped>
.dianbiao-dashboard {
  padding: 4px;
}
.toolbar-card {
  margin-bottom: 12px;
}
.last-ts {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
.stat-card {
  text-align: center;
}
.stat-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
}
.stat-unit {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}
.chart-box {
  width: 100%;
  height: 260px;
}
</style>