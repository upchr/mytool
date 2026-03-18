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
import {NButton, NTag, NSpace, NIcon} from "naive-ui"
import {AddOutline, ExtensionPuzzleOutline, TrashOutline} from "@vicons/ionicons5"
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
  {
    title: "ID",
    key: "id",
    width: 80
  },
  {
    title: "图标",
    key: "icon",
    width: 60,
    render(row) {
      return row.icon || '📦'
    }
  },
  {
    title: "插件ID",
    key: "plugin_id",
    width: 150
  },
  {
    title: "名称",
    key: "name",
    width: 150
  },
  {
    title: "版本",
    key: "version",
    width: 80
  },
  {
    title: "类型",
    key: "plugin_type",
    width: 100,
    render(row) {
      const typeMap = {
        'notification': '通知',
        'executor': '执行器',
        'datasource': '数据源'
      }
      return typeMap[row.plugin_type] || row.plugin_type
    }
  },
  {
    title: "描述",
    key: "description",
    ellipsis: { tooltip: true }
  },
  {
    title: "状态",
    key: "is_installed",
    width: 100,
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
    width: 200,
    render(row) {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: row.is_installed ? 'warning' : 'primary',
            onClick: () => handleInstall(row)
          }, { default: () => row.is_installed ? '卸载' : '安装' }),
          h(NButton, {
            size: 'small',
            onClick: () => handleEdit(row)
          }, { default: () => '编辑' }),
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row)
          }, { default: () => '删除' })
        ]
      })
    }
  }
]

// ========== 表单配置 ==========
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      {
        name: 'plugin_id',
        label: '插件ID',
        type: 'input',
        required: true,
        maxlength: 100,
        disabled: dialogType.value === 'edit'
      },
      {
        name: 'name',
        label: '名称',
        type: 'input',
        required: true,
        maxlength: 100
      },
      {
        name: 'version',
        label: '版本',
        type: 'input',
        maxlength: 20
      },
      {
        name: 'author',
        label: '作者',
        type: 'input',
        maxlength: 100
      },
      {
        name: 'description',
        label: '描述',
        type: 'textarea',
        autosize: { minRows: 2, maxRows: 4 }
      },
      {
        name: 'plugin_type',
        label: '类型',
        type: 'select',
        options: typeOptions
      },
      {
        name: 'icon',
        label: '图标',
        type: 'input',
        maxlength: 10
      },
      {
        name: 'entry_point',
        label: '入口点',
        type: 'input',
        placeholder: 'module_path:ClassName'
      },
      {
        name: 'is_official',
        label: '官方插件',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false
      },
      {
        name: 'is_active',
        label: '启用',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false
      }
    ]
  }
])

// 验证规则
const formRules = (model) => ({
  plugin_id: [{ required: true, message: '请输入插件ID', trigger: ['blur', 'input'] }],
  name: [{ required: true, message: '请输入名称', trigger: ['blur', 'input'] }]
})

// ========== 方法定义 ==========

/**
 * 加载插件列表
 */
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

/**
 * 新增插件
 */
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = { ...defaultFormData }
  showDialog.value = true
}

/**
 * 编辑插件
 */
const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = { ...row }
  showDialog.value = true
}

/**
 * 删除插件
 */
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

/**
 * 安装/卸载插件
 */
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
  } catch (e) {
    // 错误已自动处理
  }
}

/**
 * 提交表单
 */
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

/**
 * 取消
 */
const handleCancel = () => {
  showDialog.value = false
}

// ========== 生命周期 ==========
onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
</style>
