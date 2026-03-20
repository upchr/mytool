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
          请根据对应格式填写配置信息
        </n-text>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useBreakpoints } from '@vueuse/core'
import DialogForm from '@/components/DialogForm.vue'
import {
  Settings as SettingsIcon,
  Pencil as EditIcon,
  CheckmarkCircle as CheckIcon,
  CloseCircle as CloseIcon,
  ChatbubbleOutline
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

// 表单字段配置
const formFields = [
  {
    name: 'service_name',
    label: '渠道名称',
    type: 'input',
    placeholder: `如：我的${props.service.service_name}`,
  },
  {
    name: 'config',
    label: '配置 (JSON)',
    type: 'textarea',
    placeholder: props.config,
    autosize: {
      minRows: 5,
      maxRows: 10,
    }
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
  ],
  config: [
    { required: true, message: '请输入配置 JSON', trigger: 'blur' },
    {
      validator: (rule, value) => {
        if (!value) return true
        try {
          JSON.parse(value)
          return true
        } catch (e) {
          return false
        }
      },
      message: '请输入有效的 JSON 格式',
      trigger: 'blur'
    }
  ],
}

// 获取服务配置
const getService = async (serviceId) => {
  try {
    const res = await window.$request.get(`/notifications/services/${serviceId}`)
    formData.value = { ...res }
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
    data.config = JSON.parse(data.config)
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
