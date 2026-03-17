<template>
  <n-card title="AI 知识库管理" class="knowledge-card">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索知识库名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
      </n-space>

      <n-space>
        <n-button type="info" @click="handleRefresh">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>

        <n-button type="primary" @click="handleCreateBase">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建知识库
        </n-button>
      </n-space>
    </n-space>

    <!-- 知识库列表 -->
    <n-data-table
        :columns="baseColumns"
        :data="baseList"
        :loading="loading"
        :pagination="basePagination"
        :bordered="false"
        :row-key="row => row.id"
        remote
        @update:page="handleBasePageChange"
        @update:page-size="handleBasePageSizeChange"
    />

    <!-- 新建/编辑知识库对话框 -->
    <DialogForm
        ref="baseDialogRef"
        dialogPreset="card"
        v-model:visible="showBaseDialog"
        v-model:formData="baseFormData"
        :use-field-groups="true"
        :field-groups="baseFieldGroups"
        :rules="baseRules"
        :title="baseDialogTitle"
        :positive-text="baseDialogType === 'add' ? '创建' : '更新'"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="保存成功！"
        @submit="handleSubmitBase"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" @click="handleCancelBase">取消</n-button>
          <n-button
              size="small"
              type="success"
              :loading="submitting"
              @click="handleSubmitBase(formData, true)"
          >
            确定
          </n-button>
        </n-space>
      </template>
    </DialogForm>

    <!-- 文档管理对话框 -->
    <n-modal
        v-model:show="showDocumentDialog"
        preset="card"
        :title="`知识库文档 - ${currentBase?.name || ''}`"
        style="width: 900px"
        :bordered="false"
    >
      <n-space vertical style="margin-bottom: 16px">
        <n-space justify="space-between">
          <n-input
              v-model:value="docSearchKeyword"
              placeholder="搜索文档标题"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearchDocuments"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          <n-button type="primary" size="small" @click="handleCreateDocument">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            新建文档
          </n-button>
        </n-space>
      </n-space>

      <n-data-table
          :columns="docColumns"
          :data="documentList"
          :loading="docLoading"
          :pagination="docPagination"
          :bordered="false"
          :row-key="row => row.id"
          remote
          max-height="400"
          @update:page="handleDocPageChange"
          @update:page-size="handleDocPageSizeChange"
      />

      <template #footer>
        <n-space justify="end">
          <n-button @click="showDocumentDialog = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 新建/编辑文档对话框 -->
    <DialogForm
        ref="docDialogRef"
        dialogPreset="card"
        v-model:visible="showDocFormDialog"
        v-model:formData="docFormData"
        :use-field-groups="true"
        :field-groups="docFieldGroups"
        :rules="docRules"
        :title="docDialogTitle"
        :positive-text="docDialogType === 'add' ? '创建' : '更新'"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="保存成功！"
        @submit="handleSubmitDocument"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" @click="handleCancelDoc">取消</n-button>
          <n-button
              size="small"
              type="success"
              :loading="submitting"
              @click="handleSubmitDocument(formData, true)"
          >
            确定
          </n-button>
        </n-space>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import {h, ref, reactive, computed, onMounted} from 'vue'
import {
  NCard, NSpace, NButton, NInput, NIcon, NDataTable,
  NModal, NTag
} from 'naive-ui'
import {
  AddOutline,
  RefreshOutline,
  SearchOutline,
  DocumentTextOutline,
  CreateOutline,
  TrashOutline,
  FolderOpenOutline
} from '@vicons/ionicons5'
import DialogForm from '@/components/DialogForm.vue'

// ========== 状态定义 ==========
const loading = ref(false)
const docLoading = ref(false)
const submitting = ref(false)
const baseList = ref([])
const documentList = ref([])
const searchKeyword = ref('')
const docSearchKeyword = ref('')
const currentBase = ref(null)
const showBaseDialog = ref(false)
const showDocumentDialog = ref(false)
const showDocFormDialog = ref(false)
const baseDialogType = ref('add')
const docDialogType = ref('add')
const baseDialogRef = ref(null)
const docDialogRef = ref(null)

// 分页配置
const basePagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30],
  prefix: ({itemCount}) => `总共 ${itemCount} 条`
})

const docPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30],
  prefix: ({itemCount}) => `总共 ${itemCount} 条`
})

// 表单数据
const baseFormData = ref({
  name: '',
  description: ''
})

const defaultBaseFormData = {
  name: '',
  description: ''
}

const docFormData = ref({
  knowledge_base_id: null,
  title: '',
  content: '',
  category: '',
  tags: ''
})

const defaultDocFormData = {
  knowledge_base_id: null,
  title: '',
  content: '',
  category: '',
  tags: ''
}

// 计算属性
const baseDialogTitle = computed(() => {
  return baseDialogType.value === 'add' ? '新建知识库' : '编辑知识库'
})

const docDialogTitle = computed(() => {
  return docDialogType.value === 'add' ? '新建文档' : '编辑文档'
})

// 知识库表格列
const baseColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '知识库名称',
    key: 'name',
    width: 200,
    ellipsis: {tooltip: true}
  },
  {
    title: '描述',
    key: 'description',
    width: 300,
    ellipsis: {tooltip: true}
  },
  {
    title: '文档数量',
    key: 'doc_count',
    width: 100,
    render: (row) => {
      return documentList.value.filter(d => d.knowledge_base_id === row.id).length
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render: (row) => {
      return h(NTag, {
        type: row.is_active ? 'success' : 'default',
        bordered: false,
        size: 'small'
      }, {default: () => row.is_active ? '启用' : '禁用'})
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    render: (row) => {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render: (row) => {
      return h(NSpace, {size: 'small'}, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: 'small',
            type: 'info',
            onClick: () => handleViewDocuments(row)
          }, {
            default: () => '文档',
            icon: () => h(NIcon, null, {default: () => h(FolderOpenOutline)})
          }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: 'small',
            type: 'primary',
            onClick: () => handleEditBase(row)
          }, {default: () => '编辑'}),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: 'small',
            type: 'error',
            onClick: () => handleDeleteBase(row)
          }, {default: () => '删除'})
        ]
      })
    }
  }
]

// 文档表格列
const docColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '文档标题',
    key: 'title',
    width: 200,
    ellipsis: {tooltip: true}
  },
  {
    title: '分类',
    key: 'category',
    width: 120,
    render: (row) => {
      return row.category || '-'
    }
  },
  {
    title: '标签',
    key: 'tags',
    width: 150,
    render: (row) => {
      if (!row.tags) return '-'
      const tags = row.tags.split(',').filter(t => t.trim())
      return h(NSpace, {size: 'small'}, {
        default: () => tags.map(tag =>
          h(NTag, {
            type: 'info',
            bordered: false,
            size: 'small'
          }, {default: () => tag.trim()})
        )
      })
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render: (row) => {
      return h(NTag, {
        type: row.is_active ? 'success' : 'default',
        bordered: false,
        size: 'small'
      }, {default: () => row.is_active ? '启用' : '禁用'})
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    render: (row) => {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => {
      return h(NSpace, {size: 'small'}, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: 'small',
            type: 'primary',
            onClick: () => handleEditDocument(row)
          }, {
            default: () => '编辑',
            icon: () => h(NIcon, null, {default: () => h(CreateOutline)})
          }),
          h(NButton, {
            strong: true,
            tertiary: true,
            size: 'small',
            type: 'error',
            onClick: () => handleDeleteDocument(row)
          }, {
            default: () => '删除',
            icon: () => h(NIcon, null, {default: () => h(TrashOutline)})
          })
        ]
      })
    }
  }
]

// 知识库表单字段分组
const baseFieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      {
        name: 'name',
        label: '知识库名称',
        type: 'input',
        placeholder: '请输入知识库名称',
        required: true,
        maxlength: 100
      },
      {
        name: 'description',
        label: '描述',
        type: 'textarea',
        placeholder: '请输入知识库描述',
        autosize: {minRows: 3, maxRows: 6},
        maxlength: 500
      }
    ]
  }
])

// 文档表单字段分组
const docFieldGroups = computed(() => [
  {
    title: '文档信息',
    fields: [
      {
        name: 'title',
        label: '文档标题',
        type: 'input',
        placeholder: '请输入文档标题',
        required: true,
        maxlength: 255
      },
      {
        name: 'category',
        label: '分类',
        type: 'input',
        placeholder: '请输入文档分类',
        maxlength: 100
      },
      {
        name: 'tags',
        label: '标签',
        type: 'input',
        placeholder: '请输入标签，逗号分隔',
        maxlength: 500
      }
    ]
  },
  {
    title: '文档内容',
    fields: [
      {
        name: 'content',
        label: '内容',
        type: 'textarea',
        placeholder: '请输入文档内容，支持 Markdown 格式',
        required: true,
        autosize: {minRows: 10, maxRows: 20},
        maxlength: 10000,
        showCount: true
      }
    ]
  }
])

// 验证规则
const baseRules = (model) => ({
  name: [
    {required: true, message: '请输入知识库名称', trigger: ['blur', 'input']},
    {min: 2, max: 100, message: '长度在2-100个字符', trigger: ['blur', 'input']}
  ]
})

const docRules = (model) => ({
  title: [
    {required: true, message: '请输入文档标题', trigger: ['blur', 'input']},
    {min: 2, max: 255, message: '长度在2-255个字符', trigger: ['blur', 'input']}
  ],
  content: [
    {required: true, message: '请输入文档内容', trigger: ['blur']},
    {min: 10, max: 10000, message: '长度在10-10000个字符', trigger: ['blur']}
  ]
})

// ========== 工具函数 ==========
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ========== API 调用 ==========
const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const data = await window.$request.get('/ai-chat/knowledge-base')
    baseList.value = data || []
  } catch (error) {
    console.error('加载知识库列表失败:', error)
    window.$message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const createKnowledgeBase = async () => {
  submitting.value = true
  try {
    await window.$request.post('/ai-chat/knowledge-base', baseFormData.value)
    window.$message.success('创建成功')
    showBaseDialog.value = false
    loadKnowledgeBases()
  } catch (error) {
    console.error('创建失败:', error)
    window.$message.error(error.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const updateKnowledgeBase = async () => {
  submitting.value = true
  try {
    await window.$request.put(`/ai-chat/knowledge-base/${baseFormData.value.id}`, baseFormData.value)
    window.$message.success('更新成功')
    showBaseDialog.value = false
    loadKnowledgeBases()
  } catch (error) {
    console.error('更新失败:', error)
    window.$message.error(error.response?.data?.message || '更新失败')
  } finally {
    submitting.value = false
  }
}

const deleteKnowledgeBase = async (baseId) => {
  try {
    await window.$request.delete(`/ai-chat/knowledge-base/${baseId}`)
    window.$message.success('删除成功')
    loadKnowledgeBases()
  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

const loadDocuments = async (baseId) => {
  docLoading.value = true
  try {
    const data = await window.$request.get(`/ai-chat/knowledge-base/${baseId}/documents`)
    documentList.value = data || []
  } catch (error) {
    console.error('加载文档列表失败:', error)
    window.$message.error('加载失败')
  } finally {
    docLoading.value = false
  }
}

const createDocument = async () => {
  submitting.value = true
  try {
    await window.$request.post(`/ai-chat/knowledge-base/${currentBase.value.id}/documents`, docFormData.value)
    window.$message.success('创建成功')
    showDocFormDialog.value = false
    loadDocuments(currentBase.value.id)
  } catch (error) {
    console.error('创建失败:', error)
    window.$message.error(error.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const updateDocument = async () => {
  submitting.value = true
  try {
    await window.$request.put(`/ai-chat/documents/${docFormData.value.id}`, docFormData.value)
    window.$message.success('更新成功')
    showDocFormDialog.value = false
    loadDocuments(currentBase.value.id)
  } catch (error) {
    console.error('更新失败:', error)
    window.$message.error(error.response?.data?.message || '更新失败')
  } finally {
    submitting.value = false
  }
}

const deleteDocument = async (docId) => {
  try {
    await window.$request.delete(`/ai-chat/documents/${docId}`)
    window.$message.success('删除成功')
    loadDocuments(currentBase.value.id)
  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

// ========== 事件处理 ==========
const handleCreateBase = () => {
  baseDialogType.value = 'add'
  baseFormData.value = {...defaultBaseFormData}
  showBaseDialog.value = true
}

const handleEditBase = (row) => {
  baseDialogType.value = 'edit'
  baseFormData.value = {...row}
  showBaseDialog.value = true
}

const handleDeleteBase = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除知识库 "${row.name}" 吗？这将同时删除所有相关文档。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteKnowledgeBase(row.id)
    }
  })
}

const handleCancelBase = () => {
  showBaseDialog.value = false
  baseFormData.value = {...defaultBaseFormData}
}

const handleSubmitBase = async (data, validate = false) => {
  if (validate && baseDialogRef.value) {
    try {
      await baseDialogRef.value.validate()
    } catch (error) {
      console.log('表单验证失败:', error)
      return
    }
  }

  baseFormData.value = {...data}

  if (baseDialogType.value === 'add') {
    await createKnowledgeBase()
  } else {
    await updateKnowledgeBase()
  }
}

const handleViewDocuments = (row) => {
  currentBase.value = row
  documentList.value = []
  docSearchKeyword.value = ''
  showDocumentDialog.value = true
  loadDocuments(row.id)
}

const handleCreateDocument = () => {
  docDialogType.value = 'add'
  docFormData.value = {
    ...defaultDocFormData,
    knowledge_base_id: currentBase.value.id
  }
  showDocFormDialog.value = true
}

const handleEditDocument = (row) => {
  docDialogType.value = 'edit'
  docFormData.value = {...row}
  showDocFormDialog.value = true
}

const handleDeleteDocument = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除文档 "${row.title}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteDocument(row.id)
    }
  })
}

const handleCancelDoc = () => {
  showDocFormDialog.value = false
  docFormData.value = {...defaultDocFormData}
}

const handleSubmitDocument = async (data, validate = false) => {
  if (validate && docDialogRef.value) {
    try {
      await docDialogRef.value.validate()
    } catch (error) {
      console.log('表单验证失败:', error)
      return
    }
  }

  docFormData.value = {...data}

  if (docDialogType.value === 'add') {
    await createDocument()
  } else {
    await updateDocument()
  }
}

const handleSearch = () => {
  // 实现搜索逻辑
  loadKnowledgeBases()
}

const handleSearchDocuments = () => {
  // 实现文档搜索逻辑
  loadDocuments(currentBase.value.id)
}

const handleRefresh = () => {
  loadKnowledgeBases()
}

const handleBasePageChange = (page) => {
  basePagination.page = page
  loadKnowledgeBases()
}

const handleBasePageSizeChange = (pageSize) => {
  basePagination.pageSize = pageSize
  basePagination.page = 1
  loadKnowledgeBases()
}

const handleDocPageChange = (page) => {
  docPagination.page = page
  loadDocuments(currentBase.value.id)
}

const handleDocPageSizeChange = (pageSize) => {
  docPagination.pageSize = pageSize
  docPagination.page = 1
  loadDocuments(currentBase.value.id)
}

// ========== 初始化 ==========
onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-card {
  margin: 16px;
}
</style>