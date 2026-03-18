<template>
  <n-card title="插件市场">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索插件"
            clearable
            style="width: 200px"
            @keyup.enter="loadPlugins"
        />
        <n-select
            v-model:value="filterType"
            placeholder="类型筛选"
            clearable
            style="width: 120px"
            :options="typeOptions"
            @update:value="loadPlugins"
        />
        <n-button @click="loadPlugins">搜索</n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          添加插件
        </n-button>
      </n-space>
    </n-space>

    <!-- 数据表格 -->
    <n-data-table
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        :row-key="row => row.id"
        remote
    />

    <!-- 新增/编辑对话框 -->
    <DialogForm
        ref="dialogRef"
        dialogPreset="card"
        v-model:visible="showDialog"
        v-model:formData="formData"
        :use-field-groups="true"
        :field-groups="fieldGroups"
        :rules="formRules"
        :title="dialogTitle"
        :positive-text="dialogType === 'add' ? '添加' : '更新'"
        :validate-on-submit="true"
        @submit="handleSubmit"
    />

    <!-- 插件配置对话框 -->
    <n-modal v-model:show="showConfigModal" preset="card" title="插件配置" style="width: 500px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="Webhook地址">
          <n-input v-model:value="configForm.webhook_url" placeholder="输入Webhook地址" />
        </n-form-item>
        <n-form-item label="Secret（可选）" v-if="currentPlugin?.plugin_id === 'notification-dingtalk'">
          <n-input v-model:value="configForm.secret" placeholder="钉钉加签密钥" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showConfigModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveConfig">保存配置</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 发送通知测试对话框 -->
    <n-modal v-model:show="showSendModal" preset="card" title="发送通知测试" style="width: 500px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="标题">
          <n-input v-model:value="sendForm.title" placeholder="通知标题" />
        </n-form-item>
        <n-form-item label="内容">
          <n-input v-model:value="sendForm.content" type="textarea" placeholder="通知内容" :autosize="{ minRows: 3 }" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showSendModal = false">取消</n-button>
          <n-button type="primary" @click="handleSendNotification" :loading="sending">发送</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 执行命令测试对话框 -->
    <n-modal v-model:show="showExecuteModal" preset="card" title="执行命令测试" style="width: 600px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="命令">
          <n-input v-model:value="executeForm.command" type="textarea" placeholder="要执行的命令" :autosize="{ minRows: 3 }" />
        </n-form-item>
        <n-form-item label="超时(秒)">
          <n-input-number v-model:value="executeForm.timeout" :min="10" :max="3600" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExecuteModal = false">取消</n-button>
          <n-button type="primary" @click="handleExecuteCommand" :loading="executing">执行</n-button>
        </n-space>
      </template>
      <n-divider>执行结果</n-divider>
      <n-code v-if="executeResult" :code="executeResult" language="text" />
    </n-modal>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref, reactive, computed} from "vue"
import {NButton, NTag, NSpace, NIcon} from "naive-ui"
import {AddOutline, ExtensionPuzzleOutline, SettingsOutline, SendOutline, TerminalOutline, TrashOutline} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const searchKeyword = ref('')
const filterType = ref(null)
const showDialog = ref(false)
const dialogType = ref('add')
const dialogRef = ref(null)
const currentPlugin = ref(null)

// 配置
const showConfigModal = ref(false)
const configForm = ref({ webhook_url: '', secret: '' })

// 发送通知
const showSendModal = ref(false)
const sending = ref(false)
const sendForm = ref({ title: '测试通知', content: '这是一条测试消息' })

// 执行命令
const showExecuteModal = ref(false)
const executing = ref(false)
const executeForm = ref({ command: 'echo "Hello World"', timeout: 300 })
const executeResult = ref('')

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
  onChange: (page) => { pagination.page = page; loadPlugins() },
  onUpdatePageSize: (pageSize) => { pagination.pageSize = pageSize; loadPlugins() }
})

// 类型选项
const typeOptions = [
  { label: '通知', value: 'notification' },
  { label: '执行器', value: 'executor' },
  { label: '数据源', value: 'datasource' }
]

// 表单数据
const formData = ref({})
const defaultFormData = {
  plugin_id: '',
  name: '',
  version: '1.0.0',
  author: 'MyTool Team',
  description: '',
  plugin_type: 'notification',
  category: '',
  icon: '📦',
  entry_point: '',
  is_official: false,
  is_active: true
}

// ========== 表格列定义 ==========
const columns = [
  { title: "ID", key: "id", width: 80 },
  { title: "图标", key: "icon", width: 60, render: row => row.icon || '📦' },
  { title: "插件ID", key: "plugin_id", width: 180 },
  { title: "名称", key: "name", width: 150 },
  { title: "版本", key: "version", width: 80 },
  {
    title: "类型",
    key: "plugin_type",
    width: 100,
    render(row) {
      const typeMap = { 'notification': '通知', 'executor': '执行器', 'datasource': '数据源' }
      return typeMap[row.plugin_type] || row.plugin_type
    }
  },
  {
    title: "状态",
    key: "is_installed",
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.is_installed ? 'success' : 'default',
        size: 'small'
      }, { default: () => row.is_installed ? '已安装' : '未安装' })
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 280,
    render(row) {
      const buttons = [
        h(NButton, {
          size: 'small',
          type: row.is_installed ? 'warning' : 'primary',
          onClick: () => handleInstall(row)
        }, { default: () => row.is_installed ? '卸载' : '安装' })
      ]
      
      if (row.is_installed) {
        buttons.push(
          h(NButton, { size: 'small', onClick: () => handleConfig(row) }, {
            default: () => '配置',
            icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
          })
        )
        
        if (row.plugin_type === 'notification') {
          buttons.push(
            h(NButton, { size: 'small', type: 'success', onClick: () => handleOpenSend(row) }, {
              default: () => '发送',
              icon: () => h(NIcon, null, { default: () => h(SendOutline) })
            })
          )
        }
        
        if (row.plugin_type === 'executor') {
          buttons.push(
            h(NButton, { size: 'small', type: 'info', onClick: () => handleOpenExecute(row) }, {
              default: () => '执行',
              icon: () => h(NIcon, null, { default: () => h(TerminalOutline) })
            })
          )
        }
      }
      
      buttons.push(
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' })
      )
      
      return h(NSpace, { size: 'small' }, { default: () => buttons })
    }
  }
]

// ========== 表单配置 ==========
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      { name: 'plugin_id', label: '插件ID', type: 'input', required: true, maxlength: 100, disabled: dialogType.value === 'edit' },
      { name: 'name', label: '名称', type: 'input', required: true, maxlength: 100 },
      { name: 'version', label: '版本', type: 'input', maxlength: 20 },
      { name: 'author', label: '作者', type: 'input', maxlength: 100 },
      { name: 'description', label: '描述', type: 'textarea', autosize: { minRows: 2, maxRows: 4 } },
      { name: 'plugin_type', label: '类型', type: 'select', options: typeOptions },
      { name: 'icon', label: '图标', type: 'input', maxlength: 10 },
      { name: 'is_official', label: '官方插件', type: 'switch', checkedValue: true, uncheckedValue: false },
      { name: 'is_active', label: '启用', type: 'switch', checkedValue: true, uncheckedValue: false }
    ]
  }
])

const formRules = (model) => ({
  plugin_id: [{ required: true, message: '请输入插件ID', trigger: ['blur', 'input'] }],
  name: [{ required: true, message: '请输入名称', trigger: ['blur', 'input'] }]
})

// ========== 方法定义 ==========

const loadPlugins = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/plugins', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: searchKeyword.value,
        plugin_type: filterType.value
      }
    })
    data.value = result.items || []
    pagination.itemCount = result.total || 0
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = { ...defaultFormData }
  showDialog.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = { ...row }
  showDialog.value = true
}

const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除插件 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.delete(`/plugins/${row.plugin_id}`)
      window.$message.success('删除成功')
      loadPlugins()
    }
  })
}

const handleInstall = async (row) => {
  try {
    if (row.is_installed) {
      await window.$request.post(`/plugins/${row.plugin_id}/uninstall`)
      window.$message.success('插件已卸载')
    } else {
      await window.$request.post(`/plugins/${row.plugin_id}/install`)
      window.$message.success('插件已安装')
    }
    loadPlugins()
  } catch (e) {}
}

const handleConfig = async (row) => {
  currentPlugin.value = row
  // 加载现有配置
  try {
    const configs = await window.$request.get(`/plugins/${row.plugin_id}/configs`)
    configForm.value = { webhook_url: '', secret: '' }
    for (const c of (configs || [])) {
      configForm.value[c.config_key] = c.config_value
    }
  } catch (e) {
    configForm.value = { webhook_url: '', secret: '' }
  }
  showConfigModal.value = true
}

const handleSaveConfig = async () => {
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/install`, configForm.value)
    window.$message.success('配置保存成功')
    showConfigModal.value = false
  } catch (e) {}
}

const handleOpenSend = (row) => {
  currentPlugin.value = row
  showSendModal.value = true
}

const handleSendNotification = async () => {
  sending.value = true
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/send`, sendForm.value)
    window.$message.success('通知发送成功')
    showSendModal.value = false
  } finally {
    sending.value = false
  }
}

const handleOpenExecute = (row) => {
  currentPlugin.value = row
  executeResult.value = ''
  showExecuteModal.value = true
}

const handleExecuteCommand = async () => {
  executing.value = true
  try {
    const result = await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/execute`, executeForm.value)
    executeResult.value = JSON.stringify(result, null, 2)
  } catch (e) {
    executeResult.value = `执行失败: ${e.message}`
  } finally {
    executing.value = false
  }
}

const handleSubmit = async (data) => {
  submitting.value = true
  try {
    if (dialogType.value === 'add') {
      await window.$request.post('/plugins', data)
    } else {
      await window.$request.put(`/plugins/${data.plugin_id}`, data)
    }
    window.$message.success('保存成功')
    showDialog.value = false
    loadPlugins()
  } finally {
    submitting.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
</style>
