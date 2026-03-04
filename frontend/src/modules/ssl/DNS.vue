<template>
  <n-card title="DNS授权管理">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
        />
        <n-select
            v-model:value="filterProvider"
            placeholder="厂商筛选"
            clearable
            style="width: 120px"
            :options="providerOptions"
            @update:value="loadDNSs"
        />
        <n-select
            v-model:value="filterStatus"
            placeholder="状态筛选"
            clearable
            style="width: 100px"
            :options="statusOptions"
            @update:value="loadDNSs"
        />
        <n-button @click="resetFilters" type="warning">重置</n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          添加授权
        </n-button>
        <n-button
            type="error"
            @click="deleteAll"
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
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        :scroll-x="1200"

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
  </n-card>
</template>

<script setup>
import {h, onMounted, ref, reactive, computed} from "vue"
import {NButton, NTag, NSpace, NInput, NSelect, useDialog, NDataTable} from "naive-ui"
import {AddOutline, TrashOutline} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"


// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const checkedRowKeys = ref([])
const searchKeyword = ref('')
const filterProvider = ref(null)
const filterStatus = ref(null)

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
const providerOptions = [
  {label: '腾讯云', value: 'tencent'},
  {label: '阿里云', value: 'aliyun',disabled: true},
  {label: 'CloudFlare', value: 'cloudflare',disabled: true},
]

const statusOptions = [
  {label: '启用', value: true},
  {label: '禁用', value: false}
]

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
    sorter: (a, b) => a.id - b.id
  },
  {
    title: "名称",
    key: "name",
    width: 150,
    ellipsis: {tooltip: true}
  },
  {
    title: "厂商",
    key: "provider",
    width: 100,
    render(row) {
      const providerMap = {
        tencent: {label: '腾讯云', color: '#00a4ff'},
        aliyun: {label: '阿里云', color: '#ff6a00'},
        cloudflare: {label: 'CloudFlare', color: '#f38020'}
      }
      const info = providerMap[row.provider] || {label: row.provider, color: 'default'}
      return h(NTag, {
        type: 'info',
        bordered: false,
        style: {backgroundColor: info.color + '20', color: info.color}
      }, {default: () => info.label})
    }
  },
  {
    title: "Secret ID",
    key: "secret_id",
    width: 120,
    ellipsis: {tooltip: true},
    render(row) {
      return h('span', {style: {fontFamily: 'monospace'}}, row.secret_id || '-')
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
      }, {default: () => row.is_active ? '启用' : '禁用'})
    }
  },
  {
    title: "申请次数",
    key: "total_applications",
    width: 90,
    render(row) {
      return `${row.total_success || 0}/${row.total_applications || 0}`
    }
  },
  {
    title: "成功率",
    key: "success_rate",
    width: 80,
    render(row) {
      const total = row.total_applications || 0
      const success = row.total_success || 0
      const rate = total > 0 ? Math.round(success / total * 100) : 0
      return h('span', {
        style: {color: rate > 80 ? '#18a058' : rate > 50 ? '#f0a020' : '#d03050'}
      }, `${rate}%`)
    }
  },
  {
    title: "最后使用",
    key: "last_used_at",
    width: 120,
    render(row) {
      return row.last_used_at ? new Date(row.last_used_at).toLocaleString() : '-'
    }
  },
  {
    title: "创建时间",
    key: "created_at",
    width: 120,
    render(row) {
      return new Date(row.created_at).toLocaleString()
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 120,
    fixed: "right",
    render(row) {
      return h(NSpace, {size: 'small'}, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            onClick: () => handleEdit(row)
          }, {default: () => "编辑"}),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "error",
            onClick: () => handleDelete(row)
          }, {default: () => "删除"})
        ]
      })
    }
  }
]

// ========== 表单配置 ==========
const dialogRef = ref(null)
const showDialog = ref(false)
const dialogType = ref('add')

const formData = ref({
  name: '',
  provider: 'tencent',
  secret_id: '',
  secret_key: '',
  description: '',
  is_active: true
})

const defaultFormData = {
  name: '',
  provider: 'tencent',
  secret_id: '',
  secret_key: '',
  description: '',
  is_active: true
}

const dialogTitle = computed(() => {
  return dialogType.value === 'add' ? '添加DNS授权' : `编辑授权: ${formData.value.name || ''}`
})

// 字段分组
const fieldGroups = [
  {
    title: '基本信息',
    description: '目前仅支持腾讯云DNS',
    fields: [
      {
        name: 'name',
        label: '名称',
        type: 'input',
        placeholder: '请输入授权名称',
        span: 24
      },
      {
        name: 'provider',
        label: '厂商',
        type: 'select',
        placeholder: '请选择厂商',
        options: providerOptions,
        span: 12
      },
      {
        name: 'is_active',
        label: '状态',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false,
        span: 12,
        render: ({value}) => value ? '启用' : '禁用'
      }
    ]
  },
  {
    title: '认证信息',
    fields: [
      {
        name: 'secret_id',
        label: 'Secret ID',
        type: 'input',
        placeholder: '请输入Secret ID',
        span: 24
      },
      {
        name: 'secret_key',
        label: 'Secret Key',
        type: 'input',
        inputType: "password",
        showPasswordOn: "click",
        placeholder: '请输入Secret Key',
        span: 24
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
        autosize: {minRows: 2, maxRows: 4}
      }
    ]
  }
]

// 表单验证规则
const formRules = {
  name: [
    {required: true, message: '请输入名称', trigger: ['blur', 'input']},
    {min: 2, message: '名称至少2个字符', trigger: ['blur']}
  ],
  provider: [
    {required: true, message: '请选择厂商', trigger: ['blur', 'change']}
  ],
  secret_id: [
    {required: true, message: '请输入Secret ID', trigger: ['blur']},
    {min: 8, message: 'Secret ID至少8个字符', trigger: ['blur']}
  ],
  secret_key: [
    {required: true, message: '请输入Secret Key', trigger: ['blur']},
    {min: 8, message: 'Secret Key至少8个字符', trigger: ['blur']}
  ]
}

// ========== API 调用 ==========
const loadDNSs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (filterProvider.value) {
      params.provider = filterProvider.value
    }
    if (filterStatus.value !== null && filterStatus.value !== undefined) {
      params.is_active = filterStatus.value
    }

    const res = await window.$request.get('/ssl/dns-auth', {params})

      data.value = res.items || []
      pagination.total = res.total || 0

  } catch (error) {
    console.error('加载失败:', error)
    window.$message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const addDNS = async () => {
  submitting.value = true
  try {
    const res = await window.$request.post('/ssl/dns-auth', formData.value)
      window.$message.success('添加成功')
      showDialog.value = false
      loadDNSs()

  } catch (error) {
    console.error('添加失败:', error)
    window.$message.error(error.response?.data?.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

const updateDNS = async () => {
  submitting.value = true
  try {
    const res = await window.$request.put(`/ssl/dns-auth/${formData.value.id}`, formData.value)
      window.$message.success('更新成功')
      showDialog.value = false
      loadDNSs()
  } catch (error) {
    console.error('更新失败:', error)
    window.$message.error(error.response?.data?.message || '更新失败')
  } finally {
    submitting.value = false
  }
}

const deleteDNS = async (id) => {
  try {
    const res = await window.$request.delete(`/ssl/dns-auth/${id}`)
      window.$message.success('删除成功')
      loadDNSs()
  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

const batchDelete = async (ids) => {
  try {
    const res = await window.$request.post('/ssl/dns-auth/batch/delete', {ids})
      window.$message.success(`成功删除 ${ids.length} 个授权`)
      checkedRowKeys.value = []
      loadDNSs()
  } catch (error) {
    console.error('批量删除失败:', error)
    window.$message.error(error.response?.data?.message || '批量删除失败')
  }
}

// ========== 事件处理 ==========
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = {...defaultFormData}
  showDialog.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = {...row}
  formData.value.secret_id=''
  showDialog.value = true
}

const handleDelete = (row) => {
  window.$message.warning({
    title: '确认删除',
    content: `确定要删除 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteDNS(row.id)
    }
  })
}

const deleteAll = () => {
  if (checkedRowKeys.value.length === 0) {
    window.$message.warning('请先选择要删除的项')
    return
  }

  window.$message.warning({
    title: '批量删除',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 个授权吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await batchDelete(checkedRowKeys.value)
    }
  })
}

const handleSearch = () => {
  pagination.page = 1
  loadDNSs()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterProvider.value = null
  filterStatus.value = null
  pagination.page = 1
  loadDNSs()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadDNSs()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadDNSs()
}

const handleCancel = () => {
  showDialog.value = false
  formData.value = {...defaultFormData}
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

  formData.value = {...data}

  if (dialogType.value === 'add') {
    await addDNS()
  } else {
    await updateDNS()
  }
}

const handleFieldChange = ({fieldName, value}) => {
  // console.log(`字段 ${fieldName} 变化:`, value)
}

// ========== 初始化 ==========
onMounted(() => {
  loadDNSs()
})
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
