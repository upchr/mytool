<template>
  <n-card title="任务模板市场">
    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索模板"
            clearable
            style="width: 200px"
            @keyup.enter="loadTemplates"
        />
        <n-select
            v-model:value="filterCategory"
            placeholder="分类筛选"
            clearable
            style="width: 120px"
            :options="categoryOptions"
            @update:value="loadTemplates"
        />
        <n-button @click="loadTemplates">搜索</n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          添加模板
        </n-button>
      </n-space>
    </n-space>

    <!-- 模板卡片列表 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item v-for="template in data" :key="template.id">
        <n-card :title="template.icon + ' ' + template.name" hoverable>
          <template #header-extra>
            <n-tag v-if="template.is_official" type="success" size="small">官方</n-tag>
          </template>
          
          <p style="color: #666; margin-bottom: 12px">{{ template.description || '暂无描述' }}</p>
          
          <n-space>
            <n-tag v-for="tag in template.tags?.slice(0, 3)" :key="tag" size="small">
              {{ tag }}
            </n-tag>
          </n-space>
          
          <template #footer>
            <n-space justify="space-between">
              <n-text depth="3">
                <n-icon><DownloadOutline /></n-icon>
                {{ template.download_count || 0 }}
              </n-text>
              <n-space>
                <n-button size="small" @click="handleView(template)">查看</n-button>
                <n-button size="small" type="primary" @click="handleApply(template)">应用</n-button>
              </n-space>
            </n-space>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 分页 -->
    <n-space justify="center" style="margin-top: 16px">
      <n-pagination
          v-model:page="pagination.page"
          :page-count="Math.ceil(pagination.itemCount / pagination.pageSize)"
          @update:page="loadTemplates"
      />
    </n-space>

    <!-- 查看详情抽屉 -->
    <n-drawer v-model:show="showDrawer" width="600px">
      <n-drawer-content title="模板详情">
        <template v-if="currentTemplate">
          <n-descriptions :column="1" label-placement="left">
            <n-descriptions-item label="模板ID">{{ currentTemplate.template_id }}</n-descriptions-item>
            <n-descriptions-item label="名称">{{ currentTemplate.name }}</n-descriptions-item>
            <n-descriptions-item label="分类">{{ currentTemplate.category }}</n-descriptions-item>
            <n-descriptions-item label="脚本类型">{{ currentTemplate.script_type }}</n-descriptions-item>
            <n-descriptions-item label="默认调度">{{ currentTemplate.cron_description }}</n-descriptions-item>
          </n-descriptions>
          
          <n-divider>脚本内容</n-divider>
          <n-code :code="currentTemplate.script_content" language="bash" />
          
          <n-divider>配置项</n-divider>
          <n-form v-if="currentTemplate.config_schema?.properties" label-placement="left">
            <n-form-item
                v-for="(prop, key) in currentTemplate.config_schema.properties"
                :key="key"
                :label="prop.title || key"
            >
              <n-input
                  v-if="prop.type === 'string'"
                  v-model:value="applyVariables[key]"
                  :placeholder="prop.description"
              />
              <n-input-number
                  v-else-if="prop.type === 'integer'"
                  v-model:value="applyVariables[key]"
                  :placeholder="prop.description"
              />
            </n-form-item>
          </n-form>
        </template>
      </n-drawer-content>
    </n-drawer>

    <!-- 应用模板对话框 -->
    <DialogForm
        ref="applyDialogRef"
        dialogPreset="card"
        v-model:visible="showApplyDialog"
        v-model:formData="applyFormData"
        :use-field-groups="true"
        :field-groups="applyFieldGroups"
        :rules="applyFormRules"
        title="应用模板"
        positive-text="创建任务"
        @submit="handleApplySubmit"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" @click="showApplyDialog = false">取消</n-button>
          <n-button
              size="small"
              type="success"
              :loading="submitting"
              @click="handleApplySubmit(formData, true)"
          >
            创建
          </n-button>
        </n-space>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref, reactive, computed} from "vue"
import {NButton, NTag, NSpace, NIcon, NGrid, NGridItem, NCard, NText, NDescriptions, NDescriptionsItem, NDivider, NCode, NForm, NFormItem, NInput, NInputNumber, NDrawer, NDrawerContent, NSelect} from "naive-ui"
import {AddOutline, DownloadOutline} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const searchKeyword = ref('')
const filterCategory = ref(null)
const categoryOptions = ref([])

const showDrawer = ref(false)
const currentTemplate = ref(null)

const showApplyDialog = ref(false)
const applyDialogRef = ref(null)
const applyVariables = ref({})
const applyFormData = ref({
  node_id: 1,
  name: '',
  schedule: '',
  is_active: false
})

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 9,
  itemCount: 0
})

// ========== 应用表单配置 ==========
const applyFieldGroups = computed(() => [
  {
    title: '任务配置',
    fields: [
      {
        name: 'node_id',
        label: '节点ID',
        type: 'number',
        required: true,
        min: 1
      },
      {
        name: 'name',
        label: '任务名称',
        type: 'input',
        placeholder: '留空则使用模板名称'
      },
      {
        name: 'schedule',
        label: 'Cron表达式',
        type: 'input',
        placeholder: '留空则使用模板默认'
      },
      {
        name: 'is_active',
        label: '立即激活',
        type: 'switch',
        checkedValue: true,
        uncheckedValue: false
      }
    ]
  }
])

const applyFormRules = (model) => ({
  node_id: [{ required: true, message: '请输入节点ID', trigger: ['blur', 'input'] }]
})

// ========== 方法定义 ==========

/**
 * 加载模板列表
 */
const loadTemplates = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/task-templates', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: searchKeyword.value,
        category: filterCategory.value
      }
    })
    data.value = result.items || []
    pagination.itemCount = result.total || 0
  } finally {
    loading.value = false
  }
}

/**
 * 加载分类
 */
const loadCategories = async () => {
  try {
    const result = await window.$request.get('/task-templates/categories')
    categoryOptions.value = (result || []).map(c => ({ label: c, value: c }))
  } catch (e) {
    // 忽略错误
  }
}

/**
 * 查看模板详情
 */
const handleView = (template) => {
  currentTemplate.value = template
  // 初始化变量
  if (template.config_schema?.properties) {
    applyVariables.value = {}
    for (const [key, prop] of Object.entries(template.config_schema.properties)) {
      applyVariables.value[key] = prop.default ?? ''
    }
  }
  showDrawer.value = true
}

/**
 * 应用模板
 */
const handleApply = (template) => {
  currentTemplate.value = template
  applyFormData.value = {
    node_id: 1,
    name: '',
    schedule: template.default_cron || '',
    is_active: false
  }
  // 初始化变量
  if (template.config_schema?.properties) {
    applyVariables.value = {}
    for (const [key, prop] of Object.entries(template.config_schema.properties)) {
      applyVariables.value[key] = prop.default ?? ''
    }
  }
  showApplyDialog.value = true
}

/**
 * 提交应用
 */
const handleApplySubmit = async (formData) => {
  submitting.value = true
  try {
    await window.$request.post(`/task-templates/${currentTemplate.value.template_id}/apply`, {
      ...formData,
      variables: applyVariables.value
    })
    window.$message.success('模板应用成功，任务已创建')
    showApplyDialog.value = false
    showDrawer.value = false
  } finally {
    submitting.value = false
  }
}

/**
 * 新增模板
 */
const handleAdd = () => {
  window.$message.info('模板创建功能开发中...')
}

// ========== 生命周期 ==========
onMounted(() => {
  loadTemplates()
  loadCategories()
})
</script>

<style scoped>
</style>
