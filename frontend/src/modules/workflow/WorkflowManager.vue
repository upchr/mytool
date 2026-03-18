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
import {AddOutline, PlayOutline, GitBranchOutline, TrashOutline} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const searchKeyword = ref('')
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
  {
    title: "ID",
    key: "id",
    width: 80
  },
  {
    title: "工作流ID",
    key: "workflow_id",
    width: 150
  },
  {
    title: "名称",
    key: "name",
    width: 200
  },
  {
    title: "描述",
    key: "description",
    ellipsis: { tooltip: true }
  },
  {
    title: "调度",
    key: "schedule",
    width: 150,
    render(row) {
      return row.schedule || '-'
    }
  },
  {
    title: "状态",
    key: "is_active",
    width: 100,
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
    width: 200,
    render(row) {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            onClick: () => handleTrigger(row)
          }, {
            default: () => '执行',
            icon: () => h(NIcon, null, { default: () => h(PlayOutline) })
          }),
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
        name: 'workflow_id',
        label: '工作流ID',
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
        name: 'description',
        label: '描述',
        type: 'textarea',
        autosize: { minRows: 2, maxRows: 4 }
      },
      {
        name: 'node_id',
        label: '节点ID',
        type: 'number',
        required: true,
        min: 1
      },
      {
        name: 'schedule',
        label: 'Cron表达式',
        type: 'input',
        placeholder: '可选，用于定时触发'
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
  workflow_id: [{ required: true, message: '请输入工作流ID', trigger: ['blur', 'input'] }],
  name: [{ required: true, message: '请输入名称', trigger: ['blur', 'input'] }]
})

// ========== 方法定义 ==========

/**
 * 加载工作流列表
 */
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

/**
 * 新增工作流
 */
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = { ...defaultFormData }
  showDialog.value = true
}

/**
 * 编辑工作流
 */
const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = { ...row }
  showDialog.value = true
}

/**
 * 删除工作流
 */
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

/**
 * 触发执行
 */
const handleTrigger = async (row) => {
  try {
    await window.$request.post('/workflows/trigger', {
      workflow_id: row.workflow_id
    })
    window.$message.success('工作流已触发')
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

/**
 * 取消
 */
const handleCancel = () => {
  showDialog.value = false
}

// ========== 生命周期 ==========
onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
</style>
