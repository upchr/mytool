<template>
  <n-card title="证书仓库">
    <!-- 工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索域名"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
        />
        <n-select
            v-model:value="filterAlgorithm"
            placeholder="算法筛选"
            clearable
            style="width: 100px"
            :options="algorithmOptions"
            @update:value="loadCertificates"
        />
        <n-select
            v-model:value="filterStatus"
            placeholder="状态筛选"
            clearable
            style="width: 100px"
            :options="statusOptions"
            @update:value="loadCertificates"
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
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        :scroll-x="1200"
    />

    <!-- 查看证书详情对话框 -->
    <n-modal
        v-model:show="showDetailDialog"
        preset="card"
        title="证书详情"
        style="width: 700px"
        :bordered="false"
        :segmented="false"
    >
      <n-descriptions v-if="currentCert" :column="2" label-placement="left" bordered>
        <n-descriptions-item label="ID">{{ currentCert.id }}</n-descriptions-item>
        <n-descriptions-item label="算法">{{ currentCert.algorithm }}</n-descriptions-item>
        <n-descriptions-item label="颁发者">{{ currentCert.issuer || '-' }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="currentCert.is_active ? 'success' : 'error'" size="small">
            {{ currentCert.is_active ? '有效' : '已失效' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="生效时间" :span="1">
          {{ formatDate(currentCert.not_before) }}
        </n-descriptions-item>
        <n-descriptions-item label="过期时间" :span="1">
          <span :style="{ color: isExpiringSoon(currentCert.not_after) ? '#d03050' : 'inherit' }">
            {{ formatDate(currentCert.not_after) }}
            <n-tag v-if="isExpiringSoon(currentCert.not_after)" type="warning" size="tiny" round>
              即将过期
            </n-tag>
          </span>
        </n-descriptions-item>
        <n-descriptions-item label="域名列表" :span="2">
          <n-space wrap :size="4">
            <n-tag v-for="domain in currentCert.domains" :key="domain" size="small" type="info" bordered>
              {{ domain }}
            </n-tag>
          </n-space>
        </n-descriptions-item>
        <n-descriptions-item label="证书路径" :span="2">
          <n-ellipsis style="max-width: 500px">
            {{ currentCert.cert_path || '-' }}
          </n-ellipsis>
        </n-descriptions-item>
        <n-descriptions-item label="证书路径" :span="2">
          <n-space>
            <n-button type="info" size="small" @click="copyHandle(currentCert.cert)">复制</n-button>
            <n-input type="textarea"
                     :autosize="{
                    minRows: 4,
                    maxRows: 6,
                  }"
                     v-model:value=currentCert.cert
            />
          </n-space>
        </n-descriptions-item>
        <n-descriptions-item label="私钥路径" :span="2">
          <n-ellipsis style="max-width: 500px">
            {{ currentCert.key_path || '-' }}
          </n-ellipsis>
        </n-descriptions-item>
        <n-descriptions-item label="证书路径" :span="2">
          <n-space>
            <n-button type="info" size="small" @click="copyHandle(currentCert.key)">复制</n-button>
            <n-input type="textarea"
                     :autosize="{
                    minRows: 4,
                    maxRows: 6,
                }"
                     v-model:value=currentCert.key
            />
          </n-space>
        </n-descriptions-item>
        <n-descriptions-item label="创建时间" :span="1">
          {{ formatDate(currentCert.created_at) }}
        </n-descriptions-item>
        <n-descriptions-item label="下载次数" :span="1">
          {{ downloadCount }}
          <n-button text type="primary" size="tiny" @click="loadDownloadCount(currentCert.id)">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </n-descriptions-item>
      </n-descriptions>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showDetailDialog = false">关闭</n-button>
          <n-button type="primary" @click="handleDownload(currentCert)">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            下载证书
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 下载对话框 -->
    <DialogForm
        ref="downloadDialogRef"
        v-model:visible="showDownloadDialog"
        v-model:formData="downloadForm"
        :use-field-groups="true"
        :field-groups="downloadFieldGroups"
        :rules="downloadRules"
        title="下载证书"
        positive-text="下载"
        @submit="handleDownloadSubmit"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" @click="showDownloadDialog = false">取消</n-button>
          <n-button
              size="small"
              type="success"
              :loading="downloading"
              @click="handleDownloadSubmit(formData, true)"
          >
            下载
          </n-button>
        </n-space>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import { h, onMounted, ref, reactive, computed } from "vue"
import {
  NButton, NTag, NSpace, NInput,
  NSelect, NModal,
  NEllipsis, NIcon, NDataTable
} from "naive-ui"
import { RefreshOutline, DownloadOutline } from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"


// ========== 状态定义 ==========
const loading = ref(false)
const downloading = ref(false)
const data = ref([])
const searchKeyword = ref('')
const filterAlgorithm = ref(null)
const filterStatus = ref(null)
const currentCert = ref(null)
const downloadCount = ref(0)
const showDetailDialog = ref(false)
const showDownloadDialog = ref(false)
const downloadDialogRef = ref(null)

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  onChange: (page) => handlePageChange(page),
  onUpdatePageSize: (pageSize) => handlePageSizeChange(pageSize)
})

// 筛选选项
const algorithmOptions = [
  { label: 'RSA', value: 'RSA' },
  { label: 'ECC', value: 'ECC' }
]

const statusOptions = [
  { label: '有效', value: true },
  { label: '已失效', value: false }
]

// 下载表单
const downloadForm = ref({
  cert_id: null,
  downloaded_by: ''
})

const downloadFieldGroups = [
  {
    title: '下载信息',
    fields: [
      {
        name: 'downloaded_by',
        label: '下载者',
        type: 'input',
        placeholder: '请输入下载者标识（可选）',
        span: 24
      }
    ]
  }
]

const downloadRules = {
  downloaded_by: [
    { max: 100, message: '标识不能超过100个字符', trigger: ['blur'] }
  ]
}

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

const isExpiringSoon = (dateStr) => {
  if (!dateStr) return false
  const expDate = new Date(dateStr)
  const now = new Date()
  const daysLeft = Math.floor((expDate - now) / (1000 * 60 * 60 * 24))
  return daysLeft <= 30 && daysLeft > 0
}

// ========== 表格列定义 ==========
const columns = [
  {
    title: "ID",
    key: "id",
    width: 80,
    sorter: (a, b) => a.id - b.id
  },
  {
    title: "域名",
    key: "domains",
    width: 150,
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
        domains.length > 2 && h('span', ` +${domains.length - 2}`)
      ])
    }
  },
  {
    title: "颁发者",
    key: "issuer",
    width: 150,
    ellipsis: { tooltip: true },
    render(row) {
      return row.issuer || '-'
    }
  },
  {
    title: "算法",
    key: "algorithm",
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.algorithm === 'RSA' ? 'success' : 'warning',
        bordered: false,
        size: 'small'
      }, { default: () => row.algorithm })
    }
  },
  {
    title: "生效时间",
    key: "not_before",
    width: 150,
    render(row) {
      return formatDate(row.not_before)
    }
  },
  {
    title: "过期时间",
    key: "not_after",
    width: 150,
    render(row) {
      const expiring = isExpiringSoon(row.not_after)
      return h('span', {
        style: { color: expiring ? '#d03050' : 'inherit' }
      }, formatDate(row.not_after))
    }
  },
  {
    title: "剩余天数",
    key: "days_left",
    width: 90,
    render(row) {
      if (!row.not_after) return '-'
      const days = Math.floor((new Date(row.not_after) - new Date()) / (1000 * 60 * 60 * 24))
      const color = days > 30 ? '#18a058' : days > 7 ? '#f0a020' : '#d03050'
      return h('span', { style: { color, fontWeight: 'bold' } }, `${days}天`)
    }
  },
  {
    title: "状态",
    key: "is_active",
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.is_active ? 'success' : 'error',
        bordered: false
      }, { default: () => row.is_active ? '有效' : '失效' })
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 180,
    fixed: "right",
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "info",
            onClick: () => handleView(row)
          }, { default: () => "查看" }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "primary",
            onClick: () => handleDownloadClick(row)
          }, { default: () => "下载" }),
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

// ========== API 调用 ==========
const loadCertificates = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (filterAlgorithm.value) {
      params.algorithm = filterAlgorithm.value
    }
    if (filterStatus.value !== null && filterStatus.value !== undefined) {
      params.is_active = filterStatus.value
    }
    // 搜索域名（如果后端支持）
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    const res = await window.$request.get('/ssl/certificates', { params })

      data.value = res?.items || []
      pagination.total = res?.total || 0

  } catch (error) {
    console.error('加载证书失败:', error)
    window.$message.error('加载证书失败')
  } finally {
    loading.value = false
  }
}

const detailCertificates = async (certId) => {
  try {
    const res = await window.$request.get(`/ssl/certificates/${certId}`)
    currentCert.value = res
  } catch (error) {
    console.error('加载失败:', error)
  }
}
const loadDownloadCount = async (certId) => {
  try {
    const res = await window.$request.get(`/ssl/certificates/${certId}/downloads/count`)
      downloadCount.value = res || 0
  } catch (error) {
    console.error('加载下载次数失败:', error)
    downloadCount.value = 0
  }
}

const downloadCertificate = async (certId, downloadedBy) => {
  downloading.value = true
  try {
    const res = await window.$request.post(`/ssl/certificates/${certId}/download`, {
      downloaded_by: downloadedBy
    })

      window.$message.success('下载成功')

      // 如果是文件下载，处理文件流
      if (res?.content) {
        // 如果有文件内容，创建下载链接
        const { cert, key, fullchain } = res.content
        // 这里可以根据需要处理下载逻辑
        console.log('证书内容:', { cert, key, fullchain })
      }

      return true

  } catch (error) {
    console.error('下载失败:', error)
    window.$message.error(error.response?.data?.message || '下载失败')
    return false
  } finally {
    downloading.value = false
  }
}

const deleteCertificate = async (id) => {
  try {
    const res = await window.$request.delete(`/ssl/certificates/${id}`)
      window.$message.success('删除成功')
      loadCertificates()

  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

// ========== 事件处理 ==========
const handleView = async (row) => {
  debugger
  downloadCount.value = 0
  await detailCertificates(row.id)
  await loadDownloadCount(row.id)
  showDetailDialog.value = true
}

const handleDownloadClick = (row) => {
  downloadForm.value = {
    cert_id: row.id,
    downloaded_by: ''
  }
  showDownloadDialog.value = true
}

const handleDownload = async (row) => {
  await downloadCertificate(row.id, '')
}

const handleDownloadSubmit = async (data, validate = false) => {
  if (validate && downloadDialogRef.value) {
    try {
      await downloadDialogRef.value.validate()
    } catch (error) {
      console.log('表单验证失败:', error)
      return
    }
  }

  const success = await downloadCertificate(data.cert_id, data.downloaded_by)
  if (success) {
    showDownloadDialog.value = false
    // 刷新下载次数
    if (currentCert.value && currentCert.value.id === data.cert_id) {
      await loadDownloadCount(data.cert_id)
    }
  }
}

const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除证书 "${row.domains?.[0] || row.id}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteCertificate(row.id)
    }
  })
}

const handleSearch = () => {
  pagination.page = 1
  loadCertificates()
}

const handleRefresh = () => {
  loadCertificates()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterAlgorithm.value = null
  filterStatus.value = null
  pagination.page = 1
  loadCertificates()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadCertificates()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadCertificates()
}

const copy =  (text) => {
  window.$copyCode(text)
}
const copyHandle =  (content) => {
    copy(content)
}

// ========== 初始化 ==========
onMounted(() => {
  loadCertificates()
})
</script>

<style scoped>
.n-descriptions {
  margin-top: 16px;
}
</style>
