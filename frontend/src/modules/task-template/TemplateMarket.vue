<template>
  <div class="template-market">
    <n-card>
      <template #header>
        <n-space justify="space-between" align="center">
          <n-space align="center">
            <n-text strong style="font-size: 18px">📋 任务模板市场</n-text>
            <n-tag type="info" size="small">一键创建定时任务</n-tag>
          </n-space>
          <n-space>
            <n-button @click="initTemplates" :loading="initing" type="primary" ghost>
              初始化官方模板
            </n-button>
          </n-space>
        </n-space>
      </template>

      <!-- 使用说明 -->
      <n-alert type="info" style="margin-bottom: 16px">
        <template #header>💡 使用说明</template>
        点击「初始化官方模板」加载预置模板 → 选择模板 → 填写参数 → 应用到定时任务
      </n-alert>

      <!-- 筛选栏 -->
      <n-space style="margin-bottom: 16px">
        <n-input v-model:value="searchKeyword" placeholder="搜索模板" clearable style="width: 200px" @keyup.enter="loadTemplates" />
        <n-select v-model:value="filterCategory" placeholder="分类筛选" clearable style="width: 140px" :options="categoryOptions" @update:value="loadTemplates" />
        <n-button @click="loadTemplates">搜索</n-button>
      </n-space>

      <!-- 空状态 -->
      <n-empty v-if="!loading && data.length === 0" description="暂无模板，请点击「初始化官方模板」加载预置模板">
        <template #extra>
          <n-button type="primary" @click="initTemplates" :loading="initing">
            初始化官方模板
          </n-button>
        </template>
      </n-empty>

      <!-- 模板卡片 -->
      <n-grid v-else :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
        <n-grid-item v-for="template in data" :key="template.id">
          <n-card :title="template.icon + ' ' + template.name" hoverable size="small">
            <template #header-extra>
              <n-tag v-if="template.is_official" type="success" size="small">官方</n-tag>
            </template>
            
            <p style="color: #666; margin-bottom: 12px; min-height: 40px">{{ template.description || '暂无描述' }}</p>
            
            <n-space style="margin-bottom: 12px">
              <n-tag v-for="tag in template.tags?.slice(0, 3)" :key="tag" size="small" type="info">{{ tag }}</n-tag>
            </n-space>
            
            <n-descriptions :column="1" size="small" label-placement="left">
              <n-descriptions-item label="调度">{{ template.cron_description || '按需执行' }}</n-descriptions-item>
              <n-descriptions-item label="使用次数">{{ template.download_count || 0 }}</n-descriptions-item>
            </n-descriptions>
            
            <template #footer>
              <n-space justify="end">
                <n-button size="small" @click="handleView(template)">查看详情</n-button>
                <n-button size="small" type="primary" @click="handleApply(template)">应用模板</n-button>
              </n-space>
            </template>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 分页 -->
      <n-space v-if="data.length > 0" justify="center" style="margin-top: 16px">
        <n-pagination v-model:page="pagination.page" :page-count="Math.ceil(pagination.itemCount / pagination.pageSize)" @update:page="loadTemplates" />
      </n-space>
    </n-card>

    <!-- 查看详情抽屉 -->
    <n-drawer v-model:show="showDrawer" width="650px">
      <n-drawer-content title="模板详情">
        <template v-if="currentTemplate">
          <n-descriptions :column="1" label-placement="left" bordered>
            <n-descriptions-item label="模板ID">{{ currentTemplate.template_id }}</n-descriptions-item>
            <n-descriptions-item label="名称">{{ currentTemplate.name }}</n-descriptions-item>
            <n-descriptions-item label="分类">{{ currentTemplate.category }}</n-descriptions-item>
            <n-descriptions-item label="脚本类型">{{ currentTemplate.script_type }}</n-descriptions-item>
            <n-descriptions-item label="默认调度">{{ currentTemplate.cron_description }}</n-descriptions-item>
            <n-descriptions-item label="Cron表达式">{{ currentTemplate.default_cron }}</n-descriptions-item>
          </n-descriptions>
          
          <n-divider>脚本内容</n-divider>
          <n-code :code="currentTemplate.script_content" language="bash" />
          
          <n-divider>配置参数</n-divider>
          <n-alert v-if="!currentTemplate.config_schema?.properties" type="info">
            此模板无需配置参数
          </n-alert>
          <n-form v-else label-placement="left" label-width="120px">
            <n-form-item v-for="(prop, key) in currentTemplate.config_schema.properties" :key="key" :label="prop.title || key">
              <template v-if="prop.description">
                <n-text depth="3" style="font-size: 12px; margin-bottom: 4px">{{ prop.description }}</n-text><br>
              </template>
              <n-input v-if="prop.type === 'string'" v-model:value="applyVariables[key]" :placeholder="prop.default?.toString()" />
              <n-input-number v-else-if="prop.type === 'integer'" v-model:value="applyVariables[key]" :default-value="prop.default" />
              <n-select v-else-if="prop.enum" v-model:value="applyVariables[key]" :options="prop.enum.map(e => ({ label: e, value: e }))" :default-value="prop.default" />
            </n-form-item>
          </n-form>
        </template>
        
        <template #footer>
          <n-space justify="end">
            <n-button @click="showDrawer = false">关闭</n-button>
            <n-button type="primary" @click="handleApply(currentTemplate)">应用此模板</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <!-- 应用模板对话框 -->
    <n-modal v-model:show="showApplyModal" preset="card" title="应用模板 - 创建定时任务" style="width: 550px">
      <n-alert type="info" style="margin-bottom: 16px">
        应用模板将创建一个新的定时任务，你可以在「任务管理」中查看和编辑。
      </n-alert>
      
      <n-form label-placement="left" label-width="100px">
        <n-form-item label="目标节点" required>
          <n-input-number v-model:value="applyFormData.node_id" :min="1" style="width: 100%" />
          <n-text depth="3" style="font-size: 12px">请输入执行任务的节点ID（可在「节点管理」查看）</n-text>
        </n-form-item>
        
        <n-form-item label="任务名称">
          <n-input v-model:value="applyFormData.name" placeholder="留空则使用模板名称" />
        </n-form-item>
        
        <n-form-item label="调度时间">
          <n-input v-model:value="applyFormData.schedule" :placeholder="currentTemplate?.default_cron || '0 0 * * *'" />
          <n-text depth="3" style="font-size: 12px">{{ currentTemplate?.cron_description || 'Cron表达式，如：0 8 * * * 表示每天8点' }}</n-text>
        </n-form-item>
        
        <n-form-item label="立即激活">
          <n-switch v-model:value="applyFormData.is_active" />
          <n-text depth="3" style="font-size: 12px; margin-left: 8px">关闭后可在「任务管理」中手动激活</n-text>
        </n-form-item>
        
        <n-divider>模板参数</n-divider>
        
        <n-form-item v-for="(prop, key) in currentTemplate?.config_schema?.properties || {}" :key="key" :label="prop.title || key">
          <n-input v-if="prop.type === 'string'" v-model:value="applyVariables[key]" :placeholder="prop.default?.toString()" />
          <n-input-number v-else-if="prop.type === 'integer'" v-model:value="applyVariables[key]" />
          <n-select v-else-if="prop.enum" v-model:value="applyVariables[key]" :options="prop.enum.map(e => ({ label: e, value: e }))" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showApplyModal = false">取消</n-button>
          <n-button type="primary" @click="submitApply" :loading="applying">创建任务</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'

const loading = ref(false)
const initing = ref(false)
const applying = ref(false)
const data = ref([])
const searchKeyword = ref('')
const filterCategory = ref(null)
const categoryOptions = ref([])

const showDrawer = ref(false)
const showApplyModal = ref(false)
const currentTemplate = ref(null)
const applyVariables = ref({})
const applyFormData = ref({
  node_id: 1,
  name: '',
  schedule: '',
  is_active: false
})

const pagination = reactive({ page: 1, pageSize: 9, itemCount: 0 })

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

const loadCategories = async () => {
  try {
    const result = await window.$request.get('/task-templates/categories')
    categoryOptions.value = (result || []).map(c => ({ label: c, value: c }))
  } catch (e) {}
}

const initTemplates = async () => {
  initing.value = true
  try {
    await window.$request.post('/task-templates/init')
    window.$message.success('官方模板初始化成功')
    loadTemplates()
    loadCategories()
  } finally {
    initing.value = false
  }
}

const handleView = (template) => {
  currentTemplate.value = template
  applyVariables.value = {}
  if (template.config_schema?.properties) {
    for (const [key, prop] of Object.entries(template.config_schema.properties)) {
      applyVariables.value[key] = prop.default ?? ''
    }
  }
  showDrawer.value = true
}

const handleApply = (template) => {
  currentTemplate.value = template
  applyFormData.value = {
    node_id: 1,
    name: '',
    schedule: template.default_cron || '',
    is_active: false
  }
  applyVariables.value = {}
  if (template.config_schema?.properties) {
    for (const [key, prop] of Object.entries(template.config_schema.properties)) {
      applyVariables.value[key] = prop.default ?? ''
    }
  }
  showDrawer.value = false
  showApplyModal.value = true
}

const submitApply = async () => {
  applying.value = true
  try {
    await window.$request.post(`/task-templates/${currentTemplate.value.template_id}/apply`, {
      ...applyFormData.value,
      variables: applyVariables.value
    })
    window.$message.success('任务创建成功！可在「任务管理」中查看')
    showApplyModal.value = false
    loadTemplates()
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  loadTemplates()
  loadCategories()
})
</script>

<style scoped>
.template-market {
  padding: 0;
}
</style>
