<template>
  <n-card title="CPE 设备管理">
    <!-- 工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input v-model:value="searchKeyword" placeholder="搜索配置名称" @keyup.enter="loadConfigs" style="width: 200px" />
        <n-button @click="loadConfigs">
          <template #icon><n-icon><search-outline /></n-icon></template>
          搜索
        </n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon><n-icon><add-outline /></n-icon></template>
          新建配置
        </n-button>
      </n-space>
    </n-space>

    <!-- 配置列表 -->
    <n-data-table :columns="columns" :data="data" :loading="loading" :pagination="pagination" remote />

    <!-- 设备信息对话框 -->
    <n-modal v-model:show="showDeviceInfo" preset="card" title="设备信息" style="width: 600px">
      <n-spin :show="deviceLoading">
        <div v-if="deviceInfo" class="device-info">
          <n-descriptions label-placement="left" :column="1" bordered>
            <n-descriptions-item label="产品名称">{{ deviceInfo.product_name }}</n-descriptions-item>
            <n-descriptions-item label="设备型号">{{ deviceInfo.model_name }}</n-descriptions-item>
            <n-descriptions-item label="序列号">{{ deviceInfo.serial_number }}</n-descriptions-item>
            <n-descriptions-item label="MAC 地址">{{ deviceInfo.mac_address }}</n-descriptions-item>
            <n-descriptions-item label="软件版本">{{ deviceInfo.software_version }}</n-descriptions-item>
            <n-descriptions-item label="硬件版本">{{ deviceInfo.hardware_version }}</n-descriptions-item>
            <n-descriptions-item label="运行时间">
              <template v-if="deviceInfo.uptime">
                {{ deviceInfo.uptime.days }}天 {{ deviceInfo.uptime.hours }}小时 {{ deviceInfo.uptime.minutes }}分钟
              </template>
            </n-descriptions-item>
            <n-descriptions-item label="5G 温度">
              <n-tag :type="getTempType(deviceInfo.temperature?.temp_5g)">
                {{ deviceInfo.temperature?.temp_5g?.toFixed(1) || '-' }} ℃
              </n-tag>
            </n-descriptions-item>
          </n-descriptions>
        </div>
      </n-spin>
    </n-modal>

    <!-- 短信列表对话框 -->
    <n-modal v-model:show="showSMSList" preset="card" title="短信列表" style="width: 800px">
      <n-data-table :columns="smsColumns" :data="smsData" :loading="smsLoading" max-height="400" />
    </n-modal>

    <!-- 飞行模式对话框 -->
    <n-modal v-model:show="showAirplaneMode" preset="card" title="飞行模式" style="width: 500px">
      <n-spin :show="airplaneLoading">
        <n-space vertical>
          <n-alert type="warning" title="警告">
            开启飞行模式会导致设备断网！建议开启后自动关闭。
          </n-alert>
          
          <n-form-item label="飞行模式">
            <n-switch v-model:value="airplaneEnabled" :loading="airplaneSwitching" @update:value="handleAirplaneModeChange" />
            <n-text style="margin-left: 10px">{{ airplaneEnabled ? '已开启' : '已关闭' }}</n-text>
          </n-form-item>
          
          <n-form-item label="自动关闭">
            <n-switch v-model:value="airplaneAutoDisable" :disabled="!airplaneEnabled" />
            <n-text style="margin-left: 10px">开启后 {{ airplaneAutoDisableDelay }} 秒自动关闭</n-text>
          </n-form-item>
          
          <n-form-item label="延迟时间(秒)" v-if="airplaneAutoDisable">
            <n-input-number v-model:value="airplaneAutoDisableDelay" :min="5" :max="60" />
          </n-form-item>
        </n-space>
      </n-spin>
    </n-modal>

    <!-- 配置表单对话框 -->
    <DialogForm
      ref="dialogRef"
      v-model:visible="showDialog"
      v-model:formData="formData"
      :field-groups="fieldGroups"
      :use-field-groups="true"
      :rules="formRules"
      :title="dialogTitle"
      @submit="handleSubmit"
    />
  </n-card>
</template>

<script setup>
import { h, ref, reactive, computed, onMounted } from 'vue'
import { NButton, NSpace, NTag, NSwitch, NIcon } from 'naive-ui'
import { AddOutline, SearchOutline, InformationCircleOutline, MailOutline, PlayOutline, StopOutline, AirplaneOutline } from '@vicons/ionicons5'
import DialogForm from '@/components/DialogForm.vue'

// 状态
const loading = ref(false)
const data = ref([])
const searchKeyword = ref('')
const showDialog = ref(false)
const dialogType = ref('add')
const dialogRef = ref(null)

// 设备信息
const showDeviceInfo = ref(false)
const deviceLoading = ref(false)
const deviceInfo = ref(null)
const currentConfigId = ref(null)

// 短信
const showSMSList = ref(false)
const smsLoading = ref(false)
const smsData = ref([])

// 飞行模式
const showAirplaneMode = ref(false)
const airplaneLoading = ref(false)
const airplaneSwitching = ref(false)
const airplaneEnabled = ref(false)
const airplaneAutoDisable = ref(true)
const airplaneAutoDisableDelay = ref(10)
const currentAirplaneConfigId = ref(null)

// 监控状态
const monitorStatus = ref({ running: false, config_id: null })

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  onChange: (page) => { pagination.page = page; loadConfigs() }
})

// 表单
const formData = ref({})
const defaultFormData = {
  name: '',
  host: 'http://192.168.1.1',
  username: 'admin',
  password: '',
  is_active: true,
  auto_monitor: false,
  check_interval: 3.0,
  bark_key: '',
  bark_server: 'https://api.day.app',
  feishu_webhook: '',
  webhook_url: ''
}

// 表格列
const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '名称', key: 'name', width: 120 },
  { title: '地址', key: 'host', width: 150 },
  { title: '用户名', key: 'username', width: 80 },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render(row) {
      return h(NSwitch, {
        value: row.is_active,
        onUpdateValue: (val) => handleToggle(row, val)
      })
    }
  },
  {
    title: '监控',
    key: 'auto_monitor',
    width: 80,
    render(row) {
      const isMonitoring = monitorStatus.value.running && monitorStatus.value.config_id === row.id
      return h(NTag, { type: isMonitoring ? 'success' : 'default', size: 'small' }, {
        default: () => isMonitoring ? '监控中' : (row.auto_monitor ? '自动' : '关闭')
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    render(row) {
      const isMonitoring = monitorStatus.value.running && monitorStatus.value.config_id === row.id

      return h(NSpace, {}, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => handleViewDevice(row) }, {
            default: () => '设备信息',
            icon: () => h(NIcon, null, { default: () => h(InformationCircleOutline) })
          }),
          h(NButton, { size: 'small', onClick: () => handleViewSMS(row) }, {
            default: () => '短信',
            icon: () => h(NIcon, null, { default: () => h(MailOutline) })
          }),
          h(NButton, { size: 'small', onClick: () => handleAirplaneMode(row) }, {
            default: () => '飞行',
            icon: () => h(NIcon, null, { default: () => h(AirplaneOutline) })
          }),
          isMonitoring
            ? h(NButton, { size: 'small', type: 'warning', onClick: handleStopMonitor }, {
                default: () => '停止',
                icon: () => h(NIcon, null, { default: () => h(StopOutline) })
              })
            : h(NButton, { size: 'small', type: 'success', onClick: () => handleStartMonitor(row) }, {
                default: () => '监控',
                icon: () => h(NIcon, null, { default: () => h(PlayOutline) })
              }),
          h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' })
        ]
      })
    }
  }
]

// 短信表格列
const smsColumns = [
  { title: '时间', key: 'time', width: 160 },
  { title: '号码', key: 'phone', width: 130 },
  { title: '内容', key: 'content', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'is_read',
    width: 80,
    render(row) {
      return h(NTag, { type: row.is_read ? 'default' : 'warning', size: 'small' }, {
        default: () => row.is_read ? '已读' : '未读'
      })
    }
  }
]

// 表单配置
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      { name: 'name', label: '配置名称', type: 'input', required: true, maxlength: 100, placeholder: '如：办公室 CPE' },
      { name: 'host', label: '设备地址', type: 'input', required: true, maxlength: 255, placeholder: 'http://192.168.1.1' },
      { name: 'username', label: '用户名', type: 'input', required: true, maxlength: 100 },
      { name: 'password', label: '密码', type: 'input', inputType: 'password', showPasswordOn: 'click', required: true, maxlength: 255 }
    ]
  },
  {
    title: '监控设置',
    fields: [
      { name: 'is_active', label: '启用配置', type: 'switch', checkedValue: true, uncheckedValue: false },
      { name: 'auto_monitor', label: '自动监控', type: 'switch', checkedValue: true, uncheckedValue: false },
      { name: 'check_interval', label: '检查间隔(秒)', type: 'input-number', min: 1, max: 60 }
    ]
  },
  {
    title: '通知配置',
    fields: [
      { name: 'bark_key', label: 'Bark Key', type: 'input', maxlength: 255 },
      { name: 'bark_server', label: 'Bark 服务器', type: 'input', maxlength: 255 },
      { name: 'feishu_webhook', label: '飞书 Webhook', type: 'input', maxlength: 500 },
      { name: 'webhook_url', label: '自定义 Webhook', type: 'input', maxlength: 500 }
    ]
  }
])

// 验证规则
const formRules = (model) => ({
  name: [{ required: true, message: '请输入配置名称', trigger: ['blur', 'input'] }],
  host: [{ required: true, message: '请输入设备地址', trigger: ['blur', 'input'] }],
  username: [{ required: true, message: '请输入用户名', trigger: ['blur', 'input'] }],
  password: [{ required: true, message: '请输入密码', trigger: ['blur', 'input'] }]
})

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/cpe/configs')
    data.value = result || []
    pagination.itemCount = result?.length || 0
  } catch (e) {
    window.$message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 加载监控状态
const loadMonitorStatus = async () => {
  try {
    const result = await window.$request.get('/cpe/monitor/status')
    monitorStatus.value = result || { running: false }
  } catch (e) {
    console.error('加载监控状态失败', e)
  }
}

// 新建配置
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = { ...defaultFormData }
  showDialog.value = true
}

// 编辑配置
const handleEdit = (row) => {
  dialogType.value = 'edit'
  // 复制数据，但保留密码（编辑时不强制要求输入密码）
  formData.value = { ...row }
  // 如果密码为空，设置一个占位符让用户知道需要输入
  if (!formData.value.password) {
    formData.value.password = ''
  }
  showDialog.value = true
}

// 删除配置
const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除配置 "${row.name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.delete(`/cpe/configs/${row.id}`)
      window.$message.success('删除成功')
      loadConfigs()
    }
  })
}

// 切换状态
const handleToggle = async (row, value) => {
  await window.$request.patch(`/cpe/configs/${row.id}/toggle?is_active=${value}`)
  row.is_active = value
  window.$message.success(value ? '已启用' : '已禁用')
}

// 查看设备信息
const handleViewDevice = async (row) => {
  currentConfigId.value = row.id
  showDeviceInfo.value = true
  deviceLoading.value = true
  deviceInfo.value = null

  try {
    const result = await window.$request.get(`/cpe/configs/${row.id}/device`)
    deviceInfo.value = result
  } catch (e) {
    window.$message.error('获取设备信息失败')
  } finally {
    deviceLoading.value = false
  }
}

// 查看短信
const handleViewSMS = async (row) => {
  showSMSList.value = true
  smsLoading.value = true
  smsData.value = []

  try {
    const result = await window.$request.get(`/cpe/configs/${row.id}/sms?limit=10`)
    smsData.value = result?.items || []
  } catch (e) {
    window.$message.error('获取短信列表失败')
  } finally {
    smsLoading.value = false
  }
}

// 飞行模式
const handleAirplaneMode = async (row) => {
  currentAirplaneConfigId.value = row.id
  showAirplaneMode.value = true
  airplaneLoading.value = true

  try {
    const result = await window.$request.get(`/cpe/configs/${row.id}/airplane-mode`)
    airplaneEnabled.value = result?.enabled || false
  } catch (e) {
    window.$message.error('获取飞行模式状态失败')
  } finally {
    airplaneLoading.value = false
  }
}

// 切换飞行模式
const handleAirplaneModeChange = async (enabled) => {
  airplaneSwitching.value = true

  try {
    await window.$request.post(
      `/cpe/configs/${currentAirplaneConfigId.value}/airplane-mode?enable=${enabled}&auto_disable=${airplaneAutoDisable.value}&auto_disable_delay=${airplaneAutoDisableDelay.value}`
    )
    window.$message.success(enabled ? '飞行模式已开启' : '飞行模式已关闭')
  } catch (e) {
    window.$message.error('设置飞行模式失败')
    airplaneEnabled.value = !enabled // 恢复原状态
  } finally {
    airplaneSwitching.value = false
  }
}

// 启动监控
const handleStartMonitor = async (row) => {
  try {
    await window.$request.post(`/cpe/monitor/start/${row.id}`)
    window.$message.success('监控已启动')
    loadMonitorStatus()
  } catch (e) {
    window.$message.error('启动监控失败')
  }
}

// 停止监控
const handleStopMonitor = async () => {
  try {
    await window.$request.post('/cpe/monitor/stop')
    window.$message.success('监控已停止')
    loadMonitorStatus()
  } catch (e) {
    window.$message.error('停止监控失败')
  }
}

// 提交表单
const handleSubmit = async (data) => {
  try {
    if (dialogType.value === 'add') {
      await window.$request.post('/cpe/configs', data)
    } else {
      await window.$request.put(`/cpe/configs/${data.id}`, data)
    }
    window.$message.success('保存成功')
    showDialog.value = false
    loadConfigs()
  } catch (e) {
    window.$message.error('保存失败')
  }
}

// 获取温度标签类型
const getTempType = (temp) => {
  if (!temp) return 'default'
  if (temp < 40) return 'success'
  if (temp < 50) return 'warning'
  return 'error'
}

onMounted(() => {
  loadConfigs()
  loadMonitorStatus()
})
</script>

<style scoped>
.device-info {
  padding: 16px 0;
}
</style>
