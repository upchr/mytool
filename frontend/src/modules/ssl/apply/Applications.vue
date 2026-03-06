<template>
  <n-card title="证书申请管理">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索域名/描述"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>

        <n-select
            v-model:value="filterStatus"
            placeholder="状态筛选"
            clearable
            style="width: 100px"
            :options="statusOptions"
            @update:value="loadApplications"
        />

        <n-select
            v-model:value="filterDNSAuth"
            placeholder="DNS授权"
            clearable
            style="width: 220px"
            :options="dnsAuthOptions"
            @update:value="loadApplications"
        />

        <n-select
            v-model:value="filterAutoRenew"
            placeholder="自动续期"
            clearable
            style="width: 100px"
            :options="autoRenewOptions"
            @update:value="loadApplications"
        />

        <n-button @click="resetFilters" type="warning">重置</n-button>
      </n-space>

      <n-space>
        <n-button type="info" @click="handleRefresh">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>

                <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建申请
        </n-button>
        <n-button type="error" @click="handleDel"
                  :disabled="checkedRowKeys.length === 0"
        >
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          批量删除 ({{ checkedRowKeys.length }})
        </n-button>
      </n-space>
    </n-space>

    <!-- 数据表格 -->
    <n-data-table
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        :row-key="row => row.id"
        :scroll-x="1200"
        remote
    />

    <!-- todo 嵌套路由出口 - 显示证书详情 -->
    <router-view v-slot="{ Component }">
      <transition name="fade">
        <div v-if="Component" class="router-view-wrapper">
          <component :is="Component" />
        </div>
      </transition>
    </router-view>

    <!-- 新建/编辑申请对话框 -->
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
        :show-success-message="true"
        success-message="保存成功！"
        @submit="handleSubmit"
        @field-change="handleFieldChange"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" @click="handleCancel">取消</n-button>
          <n-button
              size="small"
              type="success"
              :loading="submitting"
              @click="handleSubmit(formData, true)"
          >
            确定
          </n-button>
        </n-space>
      </template>
    </DialogForm>

    <!-- 执行历史对话框 -->
    <n-modal class="mediaModal "
        v-model:show="showExecutionsDialog"
        preset="card"
        title="执行历史"
        style="width: 800px"
        :bordered="false"
    >
      <n-tabs type="line" animated>
        <n-tab-pane name="history" tab="执行记录">
          <n-data-table
              :columns="executionColumns"
              :data="executions"
              :loading="executionsLoading"
              :pagination="executionsPagination"
              remote
              :bordered="false"
          />
        </n-tab-pane>

        <n-tab-pane name="config" tab="申请配置">
          <n-descriptions v-if="currentApplication" bordered :column="2">
            <n-descriptions-item label="ID">{{ currentApplication.id }}</n-descriptions-item>
            <n-descriptions-item label="DNS授权">
              {{ getDNSAuthName(currentApplication.dns_auth_id) }}
            </n-descriptions-item>
            <n-descriptions-item label="算法">{{ currentApplication.algorithm }}</n-descriptions-item>
            <n-descriptions-item label="自动续期">
              <n-tag :type="currentApplication.auto_renew ? 'success' : 'default'" size="small">
                {{ currentApplication.auto_renew ? '开启' : '关闭' }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="续期提前">{{ currentApplication.renew_before }}天</n-descriptions-item>
            <n-descriptions-item label="下次续期">
              {{ formatDate(currentApplication.next_renew_at) || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="getStatusType(currentApplication.status)" size="small">
                {{ getStatusText(currentApplication.status) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="域名列表" :span="2">
              <n-space wrap :size="4">
                <n-tag
                    v-for="domain in currentApplication.domains"
                    :key="domain"
                    size="small"
                    type="info"
                >
                  {{ domain }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="描述" :span="2">
              {{ currentApplication.description || '-' }}
            </n-descriptions-item>
          </n-descriptions>
        </n-tab-pane>
      </n-tabs>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showExecutionsDialog = false">关闭</n-button>
          <n-button
              type="warning"
              @click="handleExecuteNow(currentApplication)"
              :loading="executing"
          >
            <template #icon>
              <n-icon><PlayOutline /></n-icon>
            </template>
            立即执行
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 执行详情对话框 -->
    <n-modal class="mediaModal "
        v-model:show="showExecutionDetailDialog"
        preset="card"
        title="执行详情"
        style="width: 600px"
    >
      <n-descriptions v-if="currentExecution" bordered :column="1">
        <n-descriptions-item label="执行ID">{{ currentExecution.id }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="getExecutionStatusType(currentExecution.status)" size="small">
            {{ getExecutionStatusText(currentExecution.status) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="触发方式">
          {{ currentExecution.triggered_by === 'system' ? '系统自动' : '手动触发' }}
        </n-descriptions-item>
        <n-descriptions-item label="开始时间">{{ formatDate(currentExecution.started_at) }}</n-descriptions-item>
        <n-descriptions-item label="完成时间">{{ formatDate(currentExecution.completed_at) }}</n-descriptions-item>
        <n-descriptions-item label="耗时">
          {{ calculateDuration(currentExecution.started_at, currentExecution.completed_at) }}
        </n-descriptions-item>
        <n-descriptions-item label="关联证书ID">
          <n-button
              v-if="currentExecution.cert_id"
              text
              type="primary"
              @click="goToCertificate(currentExecution.cert_id)"
          >
            {{ currentExecution.cert_id }}
          </n-button>
          <span v-else>-</span>
        </n-descriptions-item>
      </n-descriptions>

      <n-divider>执行日志</n-divider>
      <n-log
          v-if="currentExecution?.log"
          :log="currentExecution.log"
          :rows="10"
          language="text"
      />
      <n-empty v-else description="暂无日志" />

      <template #footer>
        <n-space justify="end">
          <n-button @click="showExecutionDetailDialog = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup>
import { h, onMounted, ref, reactive, computed } from "vue"
import {
  NButton, NTag, NSpace, NInput,
  NSelect, NModal, NDescriptions, NDescriptionsItem,
  NEllipsis, NIcon, NTabs, NTabPane, NDataTable,
  NDivider, NLog, NEmpty
} from "naive-ui"
import {
  AddOutline,
  TrashOutline,
  RefreshOutline,
  SearchOutline,
  PlayOutline,
  ListCircleOutline,
  DocumentTextOutline
} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"
import { useRouter } from 'vue-router'

const router = useRouter()

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const executing = ref(false)
const executionsLoading = ref(false)
const data = ref([])
const dnsAuthList = ref([])
const executions = ref([])
const checkedRowKeys = ref([])
const searchKeyword = ref('')
const filterStatus = ref(null)
const filterDNSAuth = ref(null)
const filterAutoRenew = ref(null)
const currentApplication = ref(null)
const currentExecution = ref(null)
const showDialog = ref(false)
const showExecutionsDialog = ref(false)
const showExecutionDetailDialog = ref(false)
const dialogType = ref('add')
const dialogRef = ref(null)

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
  onChange: (page) => handlePageChange(page),
  onUpdatePageSize: (pageSize) => handlePageSizeChange(pageSize)
})

// 执行历史分页
const executionsPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
  onChange: (page) => handleExecPageChange(page),
  onUpdatePageSize: (pageSize) => handleExecPageSizeChange(pageSize)
})

// 筛选选项
const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

const autoRenewOptions = [
  { label: '开启', value: true },
  { label: '关闭', value: false }
]

// DNS授权选项
const dnsAuthOptions = computed(() => {
  return dnsAuthList.value.map(item => ({
    label: `【${item.provider}】 ${item.name}`,
    value: item.id
  }))
})

// 表单数据
const formData = ref({
  dns_auth_id: null,
  domains: [''],
  algorithm: 'RSA',
  renew_before: 30,
  auto_renew: true,
  auto_notice: false,
  when_notice: 'completed',
  description: '',
  email: ''
})

const defaultFormData = {
  dns_auth_id: null,
  domains: [],
  algorithm: 'RSA',
  renew_before: 30,
  auto_renew: true,
  auto_notice: false,
  when_notice: 'completed',
  description: '',
  email: ''
}

const dialogTitle = computed(() => {
  return dialogType.value === 'add' ? '新建证书申请' : '编辑证书申请'
})

// 字段分组
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    description: '支持多个域名打包为一个证书。邮箱用于申请证书时注册验证',
    fields: [
      {
        name: 'domains',
        label: '域名',
        type: 'select',
        placeholder: '请输入域名',
        span: 24,
        filterable:true,
        tag:true,
        multiple:true,
      },
      {
        name: 'dns_auth_id',
        label: 'DNS授权',
        type: 'select',
        placeholder: '请选择DNS授权',
        options: dnsAuthOptions.value,
        span: 24,
        required: true
      },
      {
        name: 'email',
        label: '邮箱',
        type: 'input',
        placeholder: '请输入申请人邮箱',
        span: 12,
        required: true
      },
    ]
  },
  {
    title: '部署配置',
    description: '配置部署到那里',
    visible:false,
    fields: [
      {
        name: 'domains',
        label: '节点',
        type: 'select',
        placeholder: '请输入域名',
        span: 24,
        filterable:true,
        tag:true,
        multiple:true,
      },
      {
        name: 'luj1',
        label: '路径1',
        type: 'select',
        placeholder: '请选择DNS授权',
        options: dnsAuthOptions.value,
        span: 24,
        required: true
      },
      {
        name: 'lu2',
        label: '路径2',
        type: 'input',
        placeholder: '请输入申请人邮箱',
        span: 12,
        required: true
      },
    ]
  },

  {
    title: '自动续期配置',
    description: '开启自动续签时，在上次申请证书成功时会进行续签。可配置结果通知！',
    fields: [
      {
        name: 'auto_renew',
        label: '自动续期',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false,
        span: 8
      },
      {
        name: 'renew_before',
        label: '续期提前(天)',
        type: 'number',
        placeholder: '请输入天数',
        min: 1,
        max: 90,
        span: 12
      }
    ]
  },
  {
    title: '通知配置',
    description: '可配置任务执行结果通知！通知配置，见菜单“消息通知”',
    fields: [
      {
        name: 'auto_notice',
        label: '执行通知',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false,
        span: 8,
      },
      {
        name: 'when_notice',
        label: '通知时机',
        type: 'select',
        options: [
          { label: '执行完成时', value: 'completed' },
          { label: '失败时', value: 'failed' },
        ],
        span: 8,
        if: { auto_notice: true }
      }
    ]
  },
  {
    title: '其他信息',
    fields: [
      {
        name: 'description',
        label: '描述',
        type: 'textarea',
        placeholder: '请输入描述信息',
        span: 24,
        autosize: { minRows: 2, maxRows: 4 }
      }
    ]
  }
])

// 表单验证规则
const formRules = {
  dns_auth_id: [
    { required: true,type:'number', message: '请选择DNS授权', trigger: ['blur', 'change'] }
  ],
  domains: [
    { required: true, type: 'array',message: '至少添加一个域名1', trigger: ['change'] },
    {
      validator: (rule, value) => {
        if (!value || value.length === 0) return new Error('至少添加一个域名')
        debugger
        for (let domain of value) {
          if (!domain || domain.trim() === '') {
            return new Error('域名不能为空')
          }
          if (!/^(?:\*\.)?(?=.{1,253}$)(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$/.test(domain)) {
            return new Error(`域名格式不正确: ${domain}`)
          }
        }
        return true
      },
      trigger: ['blur']
    }
  ],
  renew_before: [
    { required: true, type: 'number',message: '请输入续期天数', trigger: ['blur'] },
    { type: 'number', min: 1, max: 90, message: '天数必须在1-90之间', trigger: ['blur'] }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
}

// ========== 表格列定义 ==========
const columns = [
  {
    type: "selection",
    width: 40

  },
  {
    title: "ID",
    key: "id",
    width: 80,
    sorter: (a, b) => a.id - b.id,
  },
  {
    title: "域名",
    key: "domains",
    width: 120,
    ellipsis: { tooltip: true },
    render(row) {
      const domains = Array.isArray(row.domains) ? row.domains : []
      return h('div', [
        domains.slice(0, 2).map(domain =>
            h(NTag, {
              size: 'small',
              type: 'info',
              bordered: false,
              style: { marginRight: '4px' }
            }, { default: () => domain })
        ),
        domains.length > 2 && h('span', { style: { fontSize: '12px' } }, ` +${domains.length - 2}`)
      ])
    }
  },
  {
    title: "DNS授权",
    key: "dns_auth_id",
    width: 120,
    render(row) {
      const dnsAuth = dnsAuthList.value.find(d => d.id === row.dns_auth_id)
      return dnsAuth ? dnsAuth.name : row.dns_auth_id
    }
  },
  {
    title: "邮箱",
    key: "email",
    width: 80,
    render(row) {
      return row.email
    }
  },
  {
    title: "状态",
    key: "status",
    width: 100,
    render(row) {
      const type = getStatusType(row.status)
      const text = getStatusText(row.status)
      return h(NTag, { type, bordered: false }, { default: () => text })
    }
  },
  {
    title: "自动续期",
    key: "auto_renew",
    width: 90,
    render(row) {
      return h(NTag, {
        type: row.auto_renew ? 'success' : 'default',
        bordered: false,
        size: 'small'
      }, { default: () => row.auto_renew ? '开启' : '关闭' })
    }
  },
  {
    title: "下次续期",
    key: "next_renew_at",
    width: 80,
    render(row) {
      return row.next_renew_at ? formatDate(row.next_renew_at) : '-'
    }
  },
  {
    title: "创建时间",
    key: "created_at",
    width: 80,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 150,
    fixed: "right",
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "info",
            onClick: () => handleViewExecutions(row)
          }, {
            default: () => '历史',
            icon: () => h(NIcon, null, { default: () => h(ListCircleOutline) })
          }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "primary",
            onClick: () => handleEdit(row)
          }, { default: () => "编辑" }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "warning",
            onClick: () => handleExecuteNow(row),
            disabled: row.status === 'processing'
          }, {
            default: () => '执行',
            icon: () => h(NIcon, null, { default: () => h(PlayOutline) })
          }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "error",
            onClick: () => handleDelete(row)
          }, { default: () => "删除" })
        ]
      })
    }
  }
]

// 执行历史表格列
const executionColumns = [
  {
    title: "执行ID",
    key: "id",
    width: 80
  },
  {
    title: "状态",
    key: "status",
    width: 100,
    render(row) {
      const type = getExecutionStatusType(row.status)
      const text = getExecutionStatusText(row.status)
      return h(NTag, { type, bordered: false, size: 'small' }, { default: () => text })
    }
  },
  {
    title: "触发方式",
    key: "triggered_by",
    width: 100,
    render(row) {
      return row.triggered_by === 'system' ? '系统自动' : '手动'
    }
  },
  {
    title: "开始时间",
    key: "started_at",
    width: 160,
    render(row) {
      return formatDate(row.started_at)
    }
  },
  {
    title: "完成时间",
    key: "completed_at",
    width: 160,
    render(row) {
      return formatDate(row.completed_at)
    }
  },
  {
    title: "证书ID",
    key: "cert_id",
    width: 80,
    render(row) {
      return row.cert_id ? h(NButton, {
        text: true,
        type: 'primary',
        size: 'small',
        onClick: () => goToCertificate(row.cert_id)
      }, { default: () => row.cert_id }) : '-'
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render(row) {
      return h(NButton, {
        strong: true,
        tertiary: true,
        size: "small",
        type: "info",
        onClick: () => viewExecutionDetail(row)
      }, {
        default: () => '详情',
        icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
      })
    }
  }
]

// ========== 工具函数 ==========
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getStatusType = (status) => {
  const map = {
    'pending': 'default',
    'processing': 'info',
    'completed': 'success',
    'failed': 'error'
  }
  return map[status] || 'default'
}

const getStatusText = (status) => {
  const map = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}

const getExecutionStatusType = (status) => {
  const map = {
    'pending': 'default',
    'processing': 'info',
    'success': 'success',
    'failed': 'error'
  }
  return map[status] || 'default'
}

const getExecutionStatusText = (status) => {
  const map = {
    'pending': '待执行',
    'processing': '执行中',
    'success': '成功',
    'failed': '失败'
  }
  return map[status] || status
}

const calculateDuration = (start, end) => {
  if (!start || !end) return '-'
  const startTime = new Date(start).getTime()
  const endTime = new Date(end).getTime()
  const duration = endTime - startTime
  if (duration < 1000) return `${duration}ms`
  if (duration < 60000) return `${Math.round(duration / 1000)}秒`
  return `${Math.round(duration / 60000)}分${Math.round((duration % 60000) / 1000)}秒`
}

const getDNSAuthName = (id) => {
  const dnsAuth = dnsAuthList.value.find(d => d.id === id)
  return dnsAuth ? dnsAuth.name : id
}

// ========== API 调用 ==========
const loadDNSAuths = async () => {
  try {
    const res = await window.$request.get('/ssl/dns-auth', {
      params: { page: 1, page_size: 100 }
    })
      dnsAuthList.value = res?.items || []

  } catch (error) {
    console.error('加载DNS授权失败:', error)
  }
}

const loadApplications = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    if (filterDNSAuth.value) {
      params.dns_auth_id = filterDNSAuth.value
    }
    if (filterAutoRenew.value !== null && filterAutoRenew.value !== undefined) {
      params.auto_renew = filterAutoRenew.value
    }
    if (searchKeyword.value) {
      params.domains = searchKeyword.value
    }

    const res = await window.$request.get('/ssl/applications', { params })

      data.value = res?.items || []
      pagination.itemCount = res?.total || 0
  } catch (error) {
    console.error('加载证书申请失败:', error)
    window.$message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadExecutions = async (applicationId) => {
  executionsLoading.value = true
  try {
    const params = {
      page: executionsPagination.page,
      page_size: executionsPagination.pageSize
    }

    const res = await window.$request.get(`/ssl/applications/${applicationId}/executions`, { params })
    executions.value = res.items || []
    executionsPagination.itemCount = res?.total || 0
  } catch (error) {
    console.error('加载执行历史失败:', error)
    window.$message.error('加载执行历史失败')
  } finally {
    executionsLoading.value = false
  }
}

const createApplication = async () => {
  submitting.value = true
  try {
    console.log(formData)
    const res = await window.$request.post('/ssl/applications', formData.value)
      window.$message.success('创建成功')
      showDialog.value = false
      loadApplications()
  } catch (error) {
    console.error('创建失败:', error)
    window.$message.error(error.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const updateApplication = async () => {
  submitting.value = true
  try {
    console.log(formData)

    const res = await window.$request.put(`/ssl/applications/${formData.value.id}`, formData.value)
      window.$message.success('更新成功')
      showDialog.value = false
      loadApplications()
  } catch (error) {
    console.error('更新失败:', error)
    window.$message.error(error.response?.data?.message || '更新失败')
  } finally {
    submitting.value = false
  }
}

const deleteApplication = async (id) => {
  try {
    const res = await window.$request.delete(`/ssl/applications/${id}`)
      window.$message.success('删除成功')
      loadApplications()
  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

const executeApplication = async (id) => {
  executing.value = true
  try {
    const res = await window.$request.post(`/ssl/applications/execute`, {
      application_id: id,
      triggered_by: 'manual'
    })
      window.$message.success('后台执行中，异常时10分钟后可重试~')
      // 刷新执行历史
      if (currentApplication.value && currentApplication.value.id === id) {
        await loadExecutions(id)
      }
      // 刷新申请列表
      await loadApplications()
  } catch (error) {
    console.error('执行失败:', error)
    window.$message.error(error.response?.data?.message || '执行失败')
  } finally {
    executing.value = false
  }
}

// ========== 事件处理 ==========
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = { ...defaultFormData }
  showDialog.value = true
}

// const handleDel = () => {
//   dialogType.value = 'add'
//   formData.value = { ...defaultFormData }
//   showDialog.value = true
// }
const handleDel = () => {
  if (checkedRowKeys.value.length === 0) {
    window.$message.warning('请先选择要删除的项')
    return
  }

  window.$dialog.warning({
    title: '批量删除确认',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 个证书申请吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await batchDeleteApplications()
    }
  })
}

// 批量删除API调用
const batchDeleteApplications = async () => {
  try {

    // 发送对象，ids: List[int] = Body(..., embed=True),取出。或者模型取出
    // await window.$request.post('/ssl/applications/batch', {
    //    ids: checkedRowKeys.value
    // })
    const res = await window.$request.post('/ssl/applications/batch', checkedRowKeys.value)
    window.$message.success(`${res.message }`)

    checkedRowKeys.value = [] // 清空选择
    loadApplications() // 重新加载数据
  } catch (error) {
    console.error('批量删除失败:', error)
  }
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = { ...row }
  showDialog.value = true
}

const handleViewExecutions = async (row) => {
  currentApplication.value = row
  executions.value = []
  executionsPagination.page = 1
  showExecutionsDialog.value = true
  await loadExecutions(row.id)
}

const viewExecutionDetail = (execution) => {
  currentExecution.value = execution
  showExecutionDetailDialog.value = true
}

const handleExecuteNow = (row) => {
  window.$dialog.warning({
    title: '确认执行',
    content: `确定要立即执行证书申请 "${row.domains?.[0] || row.id}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await executeApplication(row.id)
    }
  })
}

const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除证书申请 "${row.domains?.[0] || row.id}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteApplication(row.id)
    }
  })
}

const goToCertificate = (certId) => {
  router.push(`/ssl-apply/cert/${certId}`)
}

const handleSearch = () => {
  pagination.page = 1
  loadApplications()
}

const handleRefresh = () => {
  loadApplications()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterStatus.value = null
  filterDNSAuth.value = null
  filterAutoRenew.value = null
  pagination.page = 1
  loadApplications()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadApplications()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadApplications()
}
const handleExecPageChange = (page) => {
  executionsPagination.page = page
  loadExecutions(currentApplication.value.id)
}

const handleExecPageSizeChange = (pageSize) => {
  executionsPagination.pageSize = pageSize
  executionsPagination.page = 1
  loadExecutions(currentApplication.value.id)
}

const handleCancel = () => {
  showDialog.value = false
  formData.value = { ...defaultFormData }
}

const handleSubmit = async (data, validate = false) => {
  if (validate && dialogRef.value) {
    try {
      await dialogRef.value.validate()
    } catch (error) {
      console.log('表单验证失败:', error)
      return
    }
  }

  formData.value = { ...data }

  if (dialogType.value === 'add') {
    await createApplication()
  } else {
    await updateApplication()
  }
}

const handleFieldChange = ({ fieldName, value }) => {
  // console.log(`字段 ${fieldName} 变化:`, value)
}

// ========== 初始化 ==========
onMounted(async () => {
  await loadDNSAuths()
  await loadApplications()
})
</script>

<style scoped>
.n-card {
  margin: 16px;
}
</style>
