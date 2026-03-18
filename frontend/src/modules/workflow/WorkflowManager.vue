<template>
  <n-card title="工作流管理">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索工作流"
            clearable
            style="width: 200px"
            @keyup.enter="loadWorkflows"
        />
        <n-button @click="loadWorkflows">搜索</n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建工作流
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
        :positive-text="dialogType === 'add' ? '创建' : '更新'"
        :validate-on-submit="true"
        @submit="handleSubmit"
    />

    <!-- 执行记录抽屉 -->
    <n-drawer v-model:show="showExecutionsDrawer" width="600px">
      <n-drawer-content title="执行记录">
        <n-space vertical>
          <n-button @click="loadExecutions" size="small">刷新</n-button>
          <n-data-table
              :columns="executionColumns"
              :data="executions"
              :loading="executionsLoading"
              :bordered="false"
              size="small"
          />
        </n-space>
      </n-drawer-content>
    </n-drawer>

    <!-- 版本管理抽屉 -->
    <n-drawer v-model:show="showVersionsDrawer" width="600px">
      <n-drawer-content title="版本管理">
        <n-space vertical>
          <n-button type="primary" @click="handleCreateVersion" size="small">
            保存当前版本
          </n-button>
          <n-data-table
              :columns="versionColumns"
              :data="versions"
              :loading="versionsLoading"
              :bordered="false"
              size="small"
          />
        </n-space>
      </n-drawer-content>
    </n-drawer>

    <!-- 节点执行详情抽屉 -->
    <n-drawer v-model:show="showNodesDrawer" width="700px">
      <n-drawer-content title="节点执行详情">
        <n-data-table
            :columns="nodeExecutionColumns"
            :data="nodeExecutions"
            :loading="nodesLoading"
            :bordered="false"
            size="small"
        />
      </n-drawer-content>
    </n-drawer>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref, reactive, computed} from "vue"
import {NButton, NTag, NSpace, NIcon} from "naive-ui"
import {AddOutline, PlayOutline, TimeOutline, GitBranchOutline, EyeOutline, TrashOutline} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const searchKeyword = ref('')
const showDialog = ref(false)
const dialogType = ref('add')
const dialogRef = ref(null)

// 执行记录
const showExecutionsDrawer = ref(false)
const executionsLoading = ref(false)
const executions = ref([])
const currentWorkflowId = ref('')

// 版本管理
const showVersionsDrawer = ref(false)
const versionsLoading = ref(false)
const versions = ref([])

// 节点执行详情
const showNodesDrawer = ref(false)
const nodesLoading = ref(false)
const nodeExecutions = ref([])

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
  onChange: (page) => { pagination.page = page; loadWorkflows() },
  onUpdatePageSize: (pageSize) => { pagination.pageSize = pageSize; loadWorkflows() }
})

// 表单数据
const formData = ref({})
const defaultFormData = {
  workflow_id: '',
  name: '',
  description: '',
  node_id: 1,
  schedule: '',
  nodes: [],
  edges: [],
  is_active: true
}

// ========== 表格列定义 ==========
const columns = [
  { title: "ID", key: "id", width: 80 },
  { title: "工作流ID", key: "workflow_id", width: 150 },
  { title: "名称", key: "name", width: 180 },
  { title: "调度", key: "schedule", width: 120, render: row => row.schedule || '-' },
  {
    title: "状态",
    key: "is_active",
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.is_active ? 'success' : 'default',
        size: 'small'
      }, { default: () => row.is_active ? '启用' : '禁用' })
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 280,
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', type: 'primary', onClick: () => handleTrigger(row) }, {
            default: () => '执行',
            icon: () => h(NIcon, null, { default: () => h(PlayOutline) })
          }),
          h(NButton, { size: 'small', onClick: () => handleViewExecutions(row) }, {
            default: () => '记录',
            icon: () => h(NIcon, null, { default: () => h(TimeOutline) })
          }),
          h(NButton, { size: 'small', onClick: () => handleViewVersions(row) }, {
            default: () => '版本',
            icon: () => h(NIcon, null, { default: () => h(GitBranchOutline) })
          }),
          h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' })
        ]
      })
    }
  }
]

// 执行记录列
const executionColumns = [
  { title: "ID", key: "id", width: 60 },
  {
    title: "状态",
    key: "status",
    width: 80,
    render(row) {
      const typeMap = { success: 'success', failed: 'error', running: 'warning' }
      return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
    }
  },
  { title: "触发方式", key: "triggered_by", width: 80 },
  { title: "开始时间", key: "start_time", width: 160 },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render(row) {
      return h(NButton, { size: 'small', onClick: () => handleViewNodes(row.id) }, {
        default: () => '详情',
        icon: () => h(NIcon, null, { default: () => h(EyeOutline) })
      })
    }
  }
]

// 版本列表列
const versionColumns = [
  { title: "版本", key: "version", width: 60 },
  { title: "名称", key: "name", width: 150 },
  { title: "变更说明", key: "change_note", ellipsis: { tooltip: true } },
  { title: "创建时间", key: "created_at", width: 160 },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render(row) {
      return h(NButton, { size: 'small', type: 'warning', onClick: () => handleRestoreVersion(row.id) }, 
        { default: () => '恢复' })
    }
  }
]

// 节点执行列
const nodeExecutionColumns = [
  { title: "节点ID", key: "node_id", width: 100 },
  { title: "节点名称", key: "node_name", width: 120 },
  { title: "类型", key: "node_type", width: 80 },
  {
    title: "状态",
    key: "status",
    width: 80,
    render(row) {
      const typeMap = { success: 'success', failed: 'error', running: 'warning' }
      return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
    }
  },
  { title: "输出", key: "output", ellipsis: { tooltip: true } },
  { title: "错误", key: "error", ellipsis: { tooltip: true } }
]

// ========== 表单配置 ==========
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      { name: 'workflow_id', label: '工作流ID', type: 'input', required: true, maxlength: 100, disabled: dialogType.value === 'edit' },
      { name: 'name', label: '名称', type: 'input', required: true, maxlength: 100 },
      { name: 'description', label: '描述', type: 'textarea', autosize: { minRows: 2, maxRows: 4 } },
      { name: 'node_id', label: '节点ID', type: 'number', required: true, min: 1 },
      { name: 'schedule', label: 'Cron表达式', type: 'input', placeholder: '可选，用于定时触发' },
      { name: 'is_active', label: '启用', type: 'switch', checkedValue: true, uncheckedValue: false }
    ]
  }
])

const formRules = (model) => ({
  workflow_id: [{ required: true, message: '请输入工作流ID', trigger: ['blur', 'input'] }],
  name: [{ required: true, message: '请输入名称', trigger: ['blur', 'input'] }]
})

// ========== 方法定义 ==========

const loadWorkflows = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/workflows', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: searchKeyword.value
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
    content: `确定要删除工作流 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.delete(`/workflows/${row.workflow_id}`)
      window.$message.success('删除成功')
      loadWorkflows()
    }
  })
}

const handleTrigger = async (row) => {
  try {
    const result = await window.$request.post('/workflows/trigger', { workflow_id: row.workflow_id })
    window.$message.success(`工作流已触发，执行ID: ${result.execution_id}`)
  } catch (e) {}
}

const handleSubmit = async (data) => {
  submitting.value = true
  try {
    if (dialogType.value === 'add') {
      await window.$request.post('/workflows', data)
    } else {
      await window.$request.put(`/workflows/${data.workflow_id}`, data)
    }
    window.$message.success('保存成功')
    showDialog.value = false
    loadWorkflows()
  } finally {
    submitting.value = false
  }
}

// 执行记录
const handleViewExecutions = (row) => {
  currentWorkflowId.value = row.workflow_id
  showExecutionsDrawer.value = true
  loadExecutions()
}

const loadExecutions = async () => {
  executionsLoading.value = true
  try {
    const result = await window.$request.get(`/workflows/${currentWorkflowId.value}/executions`)
    executions.value = result || []
  } finally {
    executionsLoading.value = false
  }
}

const handleViewNodes = async (executionId) => {
  showNodesDrawer.value = true
  nodesLoading.value = true
  try {
    const result = await window.$request.get(`/workflows/executions/${executionId}/nodes`)
    nodeExecutions.value = result || []
  } finally {
    nodesLoading.value = false
  }
}

// 版本管理
const handleViewVersions = (row) => {
  currentWorkflowId.value = row.workflow_id
  showVersionsDrawer.value = true
  loadVersions()
}

const loadVersions = async () => {
  versionsLoading.value = true
  try {
    const result = await window.$request.get(`/workflows/${currentWorkflowId.value}/versions`)
    versions.value = result || []
  } finally {
    versionsLoading.value = false
  }
}

const handleCreateVersion = async () => {
  try {
    await window.$request.post(`/workflows/${currentWorkflowId.value}/versions`)
    window.$message.success('版本保存成功')
    loadVersions()
  } catch (e) {}
}

const handleRestoreVersion = async (versionId) => {
  window.$dialog.warning({
    title: '确认恢复',
    content: '确定要恢复到此版本吗？当前状态会先保存为新版本。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.post(`/workflows/${currentWorkflowId.value}/versions/restore`, { version_id: versionId })
      window.$message.success('版本恢复成功')
      loadVersions()
      loadWorkflows()
    }
  })
}

// ========== 生命周期 ==========
onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
</style>
