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
        :scroll-x="1200"
        remote
    />

    <!-- 证书详情对话框 -->
    <CertificateDetail
        v-if="showDetailDialog"
        :id="currentCert?.id"
        :visible="showDetailDialog"
        @close="showDetailDialog = false"
        @update:visible="showDetailDialog = $event"
    />

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
import { h, onMounted, ref, reactive } from "vue"
import {
  NButton, NTag, NSpace, NInput,
  NSelect, NModal, NEllipsis, NIcon, NDataTable, NCard
} from "naive-ui"
import { RefreshOutline, DownloadOutline } from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"
import CertificateDetail from "./CertificateDetail.vue"

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
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
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
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    const res = await window.$request.get('/ssl/certificates', { params })

      data.value = res?.items || []
      pagination.itemCount = res?.total || 0

  } catch (error) {
    console.error('加载证书失败:', error)
    window.$message.error('加载证书失败')
  } finally {
    loading.value = false
  }
}

const loadDownloadCount = async (certId) => {
  try {
    const res = await window.$request.get(`/ssl/certificates/${certId}/downloads/count`)
    if (res.code === 200) {
      downloadCount.value = res || 0
    } else {
      downloadCount.value = res || 0
    }
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

    if (res.code === 200) {
      window.$message.success('下载成功')
      if (res?.content) {
        console.log('证书内容:', res.content)
      }
      return true
    } else {
      window.$message.success('下载成功')
      return true
    }
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
  }
}

// ========== 事件处理 ==========
const handleView = (row) => {
  currentCert.value = row
  showDetailDialog.value = true
}

const handleDownloadClick = (row) => {
  downloadForm.value = {
    cert_id: row.id,
    downloaded_by: ''
  }
  showDownloadDialog.value = true
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
  try {
    await window.$request.exportFile(`/ssl/certificates/${data.cert_id}/download-zip`, {}, `cert.zip`);
  } catch (error) {
    window.$message.error(`导出失败`)
  }finally {
    showDownloadDialog.value = false

  }
  // const success = await downloadCertificate(data.cert_id, data.downloaded_by)
  // if (success) {
  //   showDownloadDialog.value = false
  //   if (currentCert.value && currentCert.value.id === data.cert_id) {
  //     await loadDownloadCount(data.cert_id)
  //   }
  // }
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

// ========== 初始化 ==========
onMounted(() => {
  loadCertificates()
})
</script>

<style scoped>
.n-card {
  margin: 16px;
}
</style>
