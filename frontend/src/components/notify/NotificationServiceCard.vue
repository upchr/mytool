<template>
  <n-card 
    hoverable 
    class="service-card"
    :class="{ 'configured': service.is_configured }"
  >
    <!-- 卡片头部 -->
    <template #header>
      <div class="card-header">
        <div class="icon-wrapper">
          <n-icon :component="icon" :size="isMobile ? 28 : 24" />
        </div>
        <div class="header-text">
          <div class="title">{{ title }}</div>
          <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
        </div>
      </div>
    </template>

    <!-- 卡片内容 -->
    <div class="card-content">
      <template v-if="!service.is_configured">
        <n-button 
          type="primary" 
          :size="isMobile ? 'medium' : 'small'"
          class="config-button"
          @click="showEditDialog"
        >
          <template #icon>
            <n-icon><SettingsIcon /></n-icon>
          </template>
          配置
        </n-button>
      </template>
      <template v-else>
        <n-space 
          :size="isMobile ? 12 : 8" 
          :wrap="false"
          justify="center"
          class="action-buttons"
        >
          <n-button 
            text 
            :size="isMobile ? 'medium' : 'small'"
            class="action-button"
            @click="showEditDialog"
          >
            <template #icon>
              <n-icon :size="isMobile ? 20 : 16"><EditIcon /></n-icon>
            </template>
            <span v-if="!isMobile">编辑</span>
          </n-button>
          <n-button 
            text 
            :size="isMobile ? 'medium' : 'small'"
            class="action-button"
            @click="updateServiceStatus"
          >
            <template #icon>
              <n-icon :size="isMobile ? 20 : 16">
                <component :is="service.is_enabled ? CheckIcon : CloseIcon" />
              </n-icon>
            </template>
            <span v-if="!isMobile">{{ service.is_enabled ? '已启用' : '已禁用' }}</span>
          </n-button>
        </n-space>
      </template>
    </div>

    <!-- 配置对话框 -->
    <DialogForm
      ref="dialogRef"
      :dialogPreset="dialogPreset"
      v-model:visible="dialogVisible"
      v-model:formData="formData"
      type="warning"
      :title="dialogTitle"
      :fields="formFields"
      :rules="formRules"
      :positive-text="dialogType === 'add' ? '添加' : '保存'"
      @submit="handleSubmit"
      @cancel="handleCancel"
      @field-change="handleFieldChange"
    >
      <template #icon>
        <n-icon size="20">
          <ChatbubbleOutline />
        </n-icon>
      </template>

      <!-- 动态配置表单区域 -->
      <template #default="{ formData }">
        <div class="config-form">
          <div class="config-header">
            <n-text strong>配置参数</n-text>
            <n-button size="small" type="primary" ghost @click="addField">
              <template #icon>
                <n-icon><AddIcon /></n-icon>
              </template>
              添加字段
            </n-button>
          </div>

          <div class="config-fields">
            <div
              v-for="(field, index) in configFields"
              :key="index"
              class="config-field-item"
            >
              <div class="field-row">
                <div class="field-key">
                  <n-input
                    v-model:value="field.key"
                    placeholder="字段名"
                    :disabled="field.isDefault"
                    size="small"
                  />
                </div>
                <div class="field-value">
                  <n-input
                    v-model:value="field.value"
                    placeholder="字段值"
                    type="textarea"
                    :autosize="{ minRows: 1, maxRows: 3 }"
                    size="small"
                  />
                </div>
                <div class="field-action">
                  <n-button
                    v-if="!field.isDefault"
                    text
                    type="error"
                    size="small"
                    @click="removeField(index)"
                  >
                    <template #icon>
                      <n-icon><DeleteIcon /></n-icon>
                    </template>
                  </n-button>
                </div>
              </div>
            </div>
          </div>

          <!-- JSON 预览 -->
          <div class="config-preview">
            <n-collapse>
              <n-collapse-item title="JSON 预览" name="preview">
                <n-code :code="configJsonPreview" language="json" />
              </n-collapse-item>
            </n-collapse>
          </div>
        </div>
      </template>

      <template #action="{ formData }">
        <n-space justify="end">
          <n-button size="small" type="default" @click="handleCancel">
            取消
          </n-button>
          <n-button size="small" type="primary" @click="handleSubmit(formData, true)">
            确定
          </n-button>
        </n-space>
      </template>

      <template #footer>
        <n-text depth="3" style="font-size: 12px;">
          默认字段不可删除，可添加自定义字段
        </n-text>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useBreakpoints } from '@vueuse/core'
import DialogForm from '@/components/DialogForm.vue'
import {
  Settings as SettingsIcon,
  Pencil as EditIcon,
  CheckmarkCircle as CheckIcon,
  CloseCircle as CloseIcon,
  ChatbubbleOutline,
  Add as AddIcon,
  Trash as DeleteIcon
} from '@vicons/ionicons5'

// 响应式断点
const breakpoints = useBreakpoints({
  mobile: 640,
})
const isMobile = breakpoints.smaller('mobile')

// Props
const props = defineProps({
  service: {
    type: Object,
    required: true
  },
  config: {
    type: String,
    required: true
  },
  icon: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['success'])

// 对话框状态
const dialogPreset = ref('dialog')
const dialogRef = ref(null)
const dialogVisible = ref(false)
const dialogType = ref('edit')
const editingId = ref(null)

// 对话框标题
const dialogTitle = computed(() => `编辑 ${props.title}`)

// 默认配置模板（根据服务类型）
const defaultConfigTemplates = {
  dingtalk: {
    webhook_url: { label: 'Webhook URL', placeholder: 'https://oapi.dingtalk.com/robot/send?access_token=...', required: true }
  },
  feishu: {
    webhook_url: { label: 'Webhook URL', placeholder: 'https://open.feishu.cn/open-apis/bot/v2/hook/...', required: true }
  },
  bark: {
    device_key: { label: '设备 Key', placeholder: 'xxx', required: true },
    server_url: { label: '服务器地址', placeholder: 'https://api.day.app', required: false }
  },
  email: {
    smtp_server: { label: 'SMTP 服务器', placeholder: 'smtp.example.com', required: true },
    smtp_port: { label: 'SMTP 端口', placeholder: '587', required: true },
    email_user: { label: '邮箱用户', placeholder: 'user@example.com', required: true },
    email_password: { label: '邮箱密码', placeholder: '********', required: true },
    recipient_email: { label: '收件人邮箱', placeholder: 'recipient@example.com', required: true }
  },
  wecom: {
    webhook_url: { label: 'Webhook URL', placeholder: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...', required: true }
  },
  webhook: {
    webhook_url: { label: 'Webhook URL', placeholder: 'https://...', required: true }
  }
}

// 配置字段列表
const configFields = ref([])

// 表单字段配置（移除了 config 字段）
const formFields = [
  {
    name: 'service_name',
    label: '渠道名称',
    type: 'input',
    placeholder: `如：我的${props.service.service_name}`,
  },
  {
    name: 'is_enabled',
    label: '启用状态',
    type: 'switch',
    checkedValue: true,
    uncheckedValue: false
  }
]

// 表单数据
const formData = ref({ ...props.service })

// 验证规则
const formRules = {
  service_name: [
    { required: true, message: '请输入渠道名称', trigger: 'blur' },
    { min: 2, max: 20, message: '名称长度在 2 到 20 个字符', trigger: 'blur' }
  ]
}

// 计算属性：JSON 预览
const configJsonPreview = computed(() => {
  const config = {}
  configFields.value.forEach(field => {
    if (field.key && field.value) {
      config[field.key] = field.value
    }
  })
  return JSON.stringify(config, null, 2)
})

// 初始化配置字段
const initConfigFields = (existingConfig = null) => {
  const serviceType = props.service.service_type
  const template = defaultConfigTemplates[serviceType] || {}

  // 从模板创建默认字段
  const fields = Object.keys(template).map(key => ({
    key,
    value: '',
    label: template[key].label,
    placeholder: template[key].placeholder,
    required: template[key].required,
    isDefault: true
  }))

  // 如果有已存在的配置，填充值
  if (existingConfig && typeof existingConfig === 'object') {
    fields.forEach(field => {
      if (existingConfig[field.key] !== undefined) {
        field.value = existingConfig[field.key]
      }
    })

    // 添加自定义字段（不在模板中的字段）
    Object.keys(existingConfig).forEach(key => {
      if (!template[key]) {
        fields.push({
          key,
          value: existingConfig[key],
          label: key,
          placeholder: `请输入 ${key}`,
          required: false,
          isDefault: false
        })
      }
    })
  }

  configFields.value = fields
}

// 添加字段
const addField = () => {
  configFields.value.push({
    key: '',
    value: '',
    label: '自定义字段',
    placeholder: '请输入字段值',
    required: false,
    isDefault: false
  })
}

// 删除字段
const removeField = (index) => {
  if (!configFields.value[index].isDefault) {
    configFields.value.splice(index, 1)
  }
}

// 获取服务配置
const getService = async (serviceId) => {
  try {
    const res = await window.$request.get(`/notifications/services/${serviceId}`)
    formData.value = { ...res }
    // 解析配置并初始化字段
    let config = {}
    if (res.config) {
      if (typeof res.config === 'string') {
        try {
          config = JSON.parse(res.config)
        } catch (e) {
          console.error('解析配置失败:', e)
        }
      } else {
        config = res.config
      }
    }
    initConfigFields(config)
  } catch (error) {
    window.$message.error('获取通知配置失败')
  }
}

// 显示编辑对话框
const showEditDialog = async () => {
  dialogType.value = 'edit'
  editingId.value = null
  await getService(formData.value.id)
  dialogVisible.value = true
}

// 保存配置
const saveService = async (data) => {
  try {
    // 将动态表单转换为 JSON
    const config = {}
    configFields.value.forEach(field => {
      if (field.key && field.value) {
        config[field.key] = field.value
      }
    })

    // 验证必填字段
    const serviceType = props.service.service_type
    const template = defaultConfigTemplates[serviceType] || {}
    for (const key in template) {
      if (template[key].required && !config[key]) {
        throw new Error(`${template[key].label} 为必填项`)
      }
    }

    data.config = config
    await window.$request.put(`/notifications/services/${data.id}`, data)
    window.$message.success('配置成功')
  } catch (error) {
    if (error.message) {
      window.$message.error(error.message)
      throw error
    }
    window.$message.error(`设置失败: ${error.response?.data.detail || '未知错误'}`)
    throw error
  }
}

// 更新服务状态
const updateServiceStatus = async () => {
  formData.value.is_enabled = !formData.value.is_enabled
  try {
    await window.$request.put(`/notifications/services/status/${formData.value.id}`, {
      is_enabled: formData.value.is_enabled
    })
    loadData()
  } catch (error) {
    window.$message.error('状态更新失败')
    // 恢复状态
    formData.value.is_enabled = !formData.value.is_enabled
  }
}

// 字段变动处理
const handleFieldChange = ({ fieldName, value }) => {
  // 可以在这里添加字段变动时的逻辑
}

// 取消操作
const handleCancel = () => {
  dialogVisible.value = false
}

// 提交表单
const handleSubmit = async (data, flag = false) => {
  if (flag) {
    // 自定义按钮时，验证表单
    if (dialogRef.value) {
      try {
        await dialogRef.value.validate()
      } catch (error) {
        window.$message.warning('请检查表单填写是否正确')
        return
      }
    }
  }

  formData.value = { ...data }
  try {
    await saveService(data)
    dialogVisible.value = false
    loadData()
  } catch (error) {
    // 错误已在 saveService 中处理
  }
}

// 加载数据
const loadData = () => {
  emit('success')
}

// 监听对话框可见性，初始化配置字段
watch(dialogVisible, (newVal) => {
  if (newVal) {
    // 对话框打开时，如果配置字段为空，初始化默认字段
    if (configFields.value.length === 0) {
      initConfigFields()
    }
  }
})

// 暴露方法给父组件
defineExpose({
  showEditDialog,
  updateServiceStatus,
})
</script>

<style scoped>
.service-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  min-height: 140px;
  border: 1px solid var(--n-border-color);
}

.service-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
}

.service-card.configured {
  border-color: var(--n-primary-color-hover);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.1) 0%, rgba(24, 160, 88, 0.15) 100%);
  color: #18a058;
  flex-shrink: 0;
}

.header-text {
  flex: 1;
  min-width: 0;
}

.title {
  font-weight: 600;
  font-size: 15px;
  line-height: 1.4;
  color: var(--n-text-color);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subtitle {
  font-size: 12px;
  line-height: 1.4;
  color: var(--n-text-color-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 卡片内容 */
.card-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
}

.config-button {
  width: 100%;
  font-weight: 500;
}

.action-buttons {
  width: 100%;
  display: flex;
  gap: 8px;
}

.action-button {
  flex: 1;
  font-weight: 500;
}

/* 配置表单样式 */
.config-form {
  padding: 8px 0;
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.config-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.config-field-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--n-color-modal);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
  transition: all 0.2s ease;
}

.config-field-item:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.field-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.field-key {
  flex: 0 0 150px;
}

.field-value {
  flex: 1;
}

.field-action {
  flex-shrink: 0;
}

.config-preview {
  margin-top: 16px;
}

/* 移动端适配 */
@media (max-width: 640px) {
  .service-card {
    min-height: 120px;
  }

  .card-header {
    gap: 10px;
  }

  .icon-wrapper {
    width: 44px;
    height: 44px;
    border-radius: 10px;
  }

  .title {
    font-size: 14px;
  }

  .subtitle {
    font-size: 11px;
  }

  .card-content {
    min-height: 50px;
  }

  .action-buttons {
    width: 100%;
    gap: 12px;
  }

  .action-button {
    flex: 1;
  }

  .field-row {
    flex-direction: column;
    gap: 8px;
  }

  .field-key {
    flex: 1;
  }

  .field-value {
    flex: 1;
  }
}

@media (max-width: 480px) {
  .service-card {
    min-height: 110px;
  }

  .icon-wrapper {
    width: 40px;
    height: 40px;
    border-radius: 8px;
  }

  .title {
    font-size: 13px;
  }

  .subtitle {
    font-size: 10px;
  }
}

/* 平板适配 */
@media (min-width: 641px) and (max-width: 1024px) {
  .service-card {
    min-height: 130px;
  }
}

/* 深色模式适配 */
:deep(.n-card) {
  background-color: var(--n-color-card);
}

:deep(.n-card:hover) {
  background-color: var(--n-color-card);
}

/* 动画效果 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.service-card.configured:hover {
  animation: pulse 2s ease-in-out infinite;
}
</style>
