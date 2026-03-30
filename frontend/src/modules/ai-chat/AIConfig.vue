<template>
  <div class="ai-config-container">
    <n-card title="AI 配置管理" class="config-card">
      <n-spin :show="loading">
        <!-- 配置列表 -->
        <div class="config-list-section">
          <div class="section-header">
            <h3>配置列表</h3>
            <n-button type="primary" size="small" @click="showCreateDialog">
              <template #icon>
                <n-icon :component="AddIcon" />
              </template>
              新建配置
            </n-button>
          </div>

          <n-empty v-if="configList.length === 0" description="暂无配置" />

          <n-list v-else bordered>
            <n-list-item v-for="config in configList" :key="config.id">
              <template #prefix>
                <div class="config-avatar">
                  <n-icon :size="24" :component="config.is_enabled ? CheckmarkCircleIcon : RadioIcon" />
                </div>
              </template>

              <div class="config-info">
                <div class="config-name">{{ config.name || '未命名配置' }}</div>
                <div class="config-details">
                  <span>{{ config.model }}</span>
                  <span class="divider">|</span>
                  <span>{{ config.api_base }}</span>
                </div>
                <div class="config-time">
                  更新于: {{ formatTime(config.updated_at) }}
                </div>
              </div>
              <template #suffix>
                <div class="config-actions">
                  <n-button
                      v-if="!config.is_enabled"
                      type="success"
                      size="small"
                      @click="setActiveConfig(config.id)"
                  >
                    激活
                  </n-button>
                  <n-tag v-else type="success" size="small">当前使用</n-tag>

                  <n-button
                      size="small"
                      @click="editConfig(config)"
                  >
                    编辑
                  </n-button>

                  <n-popconfirm
                      @positive-click="deleteConfig(config.id)"
                  >
                    <template #trigger>
                      <n-button size="small" type="error" :disabled="config.is_enabled && configList.length === 1">
                        删除
                      </n-button>
                    </template>
                    确定要删除此配置吗？
                  </n-popconfirm>
                </div>
              </template>
            </n-list-item>
          </n-list>
        </div>

        <n-divider />

        <div class="config-info">
          <n-alert type="info" title="配置说明" :bordered="false">
            <ul>
              <li><strong>API Key:</strong> 从 AI 服务提供商的开放平台获取，例如
                <a href="https://platform.iflow.cn/profile?tab=apiKey" target="_blank" rel="noopener noreferrer">
                  iFlow 开放平台（免费：每7天需刷新密钥）
                </a>
              </li>
              <li><strong>API Base URL:</strong> AI 服务的 API 基础地址，通常格式为 https://api.example.com/v1</li>
              <li><strong>模型名称:</strong> 具体要使用的模型，例如 gpt-5、glm-5 等</li>
              <li><strong>切换配置:</strong> 点击"激活"按钮可以切换当前使用的配置</li>
              <li>配置保存后会立即生效，无需重启服务</li>
            </ul>
          </n-alert>
        </div>
      </n-spin>
    </n-card>

    <!-- 创建/编辑对话框 -->
    <n-modal v-model:show="showDialog" :mask-closable="false" preset="card" :title="isEdit ? '编辑配置' : '新建配置'" style="width: 600px">
      <n-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-placement="left"
          label-width="120px"
      >
        <n-form-item label="配置名称" path="name">
          <n-input
              v-model:value="formData.name"
              placeholder="例如: GPT-4 配置"
          />
        </n-form-item>

        <n-form-item label="API Base URL" path="api_base">
          <n-input
              v-model:value="formData.api_base"
              placeholder="https://api.example.com/v1"
          />
        </n-form-item>

        <n-form-item label="API Key" path="api_key">
          <n-input
              v-model:value="formData.api_key"
              type="password"
              show-password-on="click"
              placeholder="请输入 API Key"
          />
        </n-form-item>
        <n-form-item label="模型名称" path="model">
          <n-select
              v-model:value="formData.model"
              :options="modelOptions"
              filterable
              tag
              placeholder="选择或输入模型名称"
          />
        </n-form-item>

        <n-form-item label="启用" path="is_enabled" v-if="isEdit">
          <n-switch v-model:value="formData.is_enabled" />
        </n-form-item>
      </n-form>

      <template #footer>
        <div class="dialog-footer">
          <n-button @click="showDialog = false">取消</n-button>
          <n-button @click="testConnection" :loading="testing" :disabled="!isFormValid">
            测试连接
          </n-button>
          <n-button type="primary" @click="saveConfig" :loading="saving">
            {{ isEdit ? '保存' : '创建' }}
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
import {
  NCard, NForm, NFormItem, NInput, NButton, NSpin,
  NDivider, NAlert, NList, NListItem, NEmpty,
  NIcon, NTag, NModal, NPopconfirm, NSelect, useMessage
} from 'naive-ui'
import {
  AddOutline as AddIcon,
  CheckmarkCircleOutline as CheckmarkCircleIcon,
  RadioOutline as RadioIcon
} from '@vicons/ionicons5'

const message = useMessage()
const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editConfigId = ref(null)

const configList = ref([])
const formData = ref({
  name: '',
  api_key: '',
  api_base: '',
  model: '',
  is_enabled: true
})

// 预设的模型选项
const modelOptions = [
  { label: 'iflow-rome-30ba3b', value: 'iflow-rome-30ba3b' },
  { label: 'qwen3-coder-plus', value: 'qwen3-coder-plus' },
  { label: 'qwen3-max', value: 'qwen3-max' },
  { label: 'deepseek-r1', value: 'deepseek-r1' }
]

const rules = {
  name: {
    required: true,
    message: '请输入配置名称',
    trigger: ['blur', 'input']
  },
  api_key: {
    required: true,
    message: '请输入 API Key',
    trigger: ['blur', 'input']
  },
  api_base: {
    required: true,
    message: '请输入 API Base URL',
    trigger: ['blur', 'input'],
    pattern: /^https?:\/\/.+/,
    message: '请输入有效的 URL 地址'
  },
  model: {
    required: true,
    message: '请选择或输入模型名称',
    trigger: ['blur', 'change']
  }
}

const isFormValid = computed(() => {
  return formData.value.name && formData.value.api_key && formData.value.api_base && formData.value.model
})

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载配置列表
const loadConfigList = async () => {
  loading.value = true
  try {
    const data = await window.$request.get('/ai-chat/config/list')
    configList.value = data || []
  } catch (error) {
    console.error('加载配置列表失败:', error)
    message.error('加载配置列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  editConfigId.value = null
  formData.value = {
    name: '',
    api_key: '',
    api_base: '',
    model: '',
    is_enabled: true
  }
  showDialog.value = true
}

// 编辑配置
const editConfig = (config) => {
  isEdit.value = true
  editConfigId.value = config.id
  formData.value = {
    name: config.name || '',
    api_key: config.api_key || '',
    api_base: config.api_base || '',
    model: config.model || '',
    is_enabled: config.is_enabled ?? true
  }
  showDialog.value = true
}

// 保存配置
const saveConfig = async () => {
  try {
    await formRef.value?.validate()
  } catch (error) {
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await window.$request.post(`/ai-chat/config/${editConfigId.value}`, formData.value)
      message.success('配置保存成功')
    } else {
      await window.$request.post('/ai-chat/config/create', formData.value)
      message.success('配置创建成功')
    }

    showDialog.value = false
    await loadConfigList()
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 测试连接
const testConnection = async () => {
  try {
    await formRef.value?.validate()
  } catch (error) {
    return
  }

  testing.value = true
  try {
    // 直接使用表单配置进行测试，不需要先保存或设置为激活状态
    const testRes = await window.$request.post('/ai-chat/config/test-connection', {
      api_key: formData.value.api_key,
      api_base: formData.value.api_base,
      model: formData.value.model,
      message: '你好，这是一个测试消息'
    })

    if (testRes.success) {
      message.success('连接测试成功！AI 响应正常')
    } else {
      message.error(`连接测试失败：${testRes.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    message.error('测试连接失败，请检查配置和网络')
  } finally {
    testing.value = false
  }
}

// 删除配置
const deleteConfig = async (configId) => {
  try {
    await window.$request.delete(`/ai-chat/config/${configId}`)
    message.success('配置删除成功')
    await loadConfigList()
  } catch (error) {
    console.error('删除配置失败:', error)
    message.error('删除配置失败')
  }
}

// 设置激活配置
const setActiveConfig = async (configId) => {
  try {
    await window.$request.post(`/ai-chat/config/${configId}/set-active`)
    const config = configList.value.find(c => c.id === configId)
    const configName = config ? config.name : configId
    message.success(`已切换到配置: ${configName}`)
    await loadConfigList()
  } catch (error) {
    console.error('切换配置失败:', error)
    message.error('切换配置失败')
  }
}

onMounted(() => {
  loadConfigList()
})
</script>

<style scoped>
.ai-config-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.config-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-list-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.config-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f5f5;
  margin-right: 12px;
}

.config-avatar :deep(.n-icon) {
  color: #1976d2;
}

.config-info {
  flex: 1;
}

.config-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.config-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.config-details .divider {
  color: #ddd;
}

.config-time {
  font-size: 12px;
  color: #999;
}

.config-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.config-info {
  margin-top: 20px;
}

.config-info ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.config-info li {
  margin: 8px 0;
  line-height: 1.6;
}

.config-info a {
  color: #1976d2;
  text-decoration: none;
}

.config-info a:hover {
  text-decoration: underline;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 深色模式适配 */
.dark .config-card {
  background: #1e1e1e;
}

.dark .config-avatar {
  background: #2d2d2d;
}

.dark .config-details {
  color: #888;
}

.dark .config-time {
  color: #666;
}

/* ==================== 移动端响应式样式 ==================== */
@media (max-width: 768px) {
  .ai-config-container {
    padding: 12px;
    max-width: 100%;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .section-header h3 {
    font-size: 15px;
  }

  /* 配置列表项优化 */
  .config-list-section :deep(.n-list-item) {
    padding: 12px;
  }

  .config-avatar {
    width: 36px;
    height: 36px;
    margin-right: 10px;
  }

  .config-name {
    font-size: 14px;
  }

  .config-details {
    font-size: 12px;
    flex-wrap: wrap;
  }

  .config-time {
    font-size: 11px;
  }

  .config-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
    margin-top: 8px;
  }

  .config-actions button {
    width: 100%;
  }

  /* 配置说明优化 */
  .config-info {
    margin-top: 16px;
  }

  .config-info :deep(.n-alert) {
    font-size: 13px;
  }

  .config-info ul {
    margin: 6px 0 0 16px;
  }

  .config-info li {
    margin: 6px 0;
    line-height: 1.5;
  }

  /* 对话框优化 */
  .ai-config-container :deep(.n-modal) {
    width: 95% !important;
    max-width: 500px !important;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 8px;
  }

  .dialog-footer button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .ai-config-container {
    padding: 8px;
  }

  .section-header h3 {
    font-size: 14px;
  }

  .config-avatar {
    width: 32px;
    height: 32px;
  }

  .config-name {
    font-size: 13px;
  }

  .config-details {
    font-size: 11px;
  }

  .config-time {
    font-size: 10px;
  }

  .config-info :deep(.n-alert) {
    font-size: 12px;
  }

  .config-info li {
    font-size: 12px;
  }
}

/* 横屏模式适配 */
@media (max-height: 600px) and (orientation: landscape) {
  .ai-config-container {
    padding: 8px;
  }

  .config-list-section {
    margin-bottom: 12px;
  }

  .section-header {
    margin-bottom: 12px;
  }
}
</style>
