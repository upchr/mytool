<template>
  <n-card hoverable style="height: 16vh;">
    <template #header>
      <div class="card-header">
        <n-icon :component="icon" size="24" />
        <div class="header-text">
          <div class="title">{{ title }}</div>
          <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
        </div>
      </div>
    </template>
    <n-space>
      <n-button v-if="!service.is_configured" type="info" size="small" @click="showEditDialog">
        + 配置
      </n-button>
      <n-space v-else>
        <n-button text size="small" @click="showEditDialog" >
          <n-tag type="info">
            编辑
          </n-tag>
        </n-button>
        <n-button text size="small" @click="updateServiceStatus" >
          <n-tag v-if="service.is_enabled" type="primary">
            已启用
          </n-tag>
          <n-tag v-else type="warning">
            已禁用
          </n-tag>
        </n-button>
      </n-space>
      <DialogForm
          v-model:visible="dialogVisible"
          v-model:formData="formData"
          type="warning"
          :title="dialogTitle"
          :fields="formFields"
          :rules="formRules"
          :positive-text="dialogType === 'add' ? '添加' : '保存'"
          @submit="handleSubmit"
          @cancel="handleCancel"
      >
        <!-- 自定义内容插槽 -->
        <template #header>
          <div style="font-weight: bold;">
            {{service.service_name}}
          </div>
        </template>
        <template #icon>
          <n-icon>
            <ChatbubbleOutline />
          </n-icon>
        </template>

      </DialogForm>
    </n-space>
  </n-card>
</template>

<script setup>
import { ref } from 'vue'
import { computed } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import {NIcon, useMessage} from 'naive-ui'
import {ChatbubbleOutline} from "@vicons/ionicons5";
import axios from "axios";
const message = useMessage()

// 父传来props
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
    required: true
  }
})
// 触发父，回调
const emit = defineEmits(['success'])


////////// 对话框调出 //////////
// 对话框状态
const dialogVisible = ref(false)
const dialogType = ref('add') // 'add' | 'edit'
const editingId = ref(null)
const item = ref(null)

// 计算标题
const dialogTitle = computed(() => {
  return dialogType.value === 'add' ? '添加用户' : '编辑用户'
})

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
    placeholder: `对应config：${props.config}`,
    rows: 3
  },
  {
    name: 'is_enabled',
    label: '状态',
    type: 'switch',
    checkedValue: true,
    uncheckedValue: false
  },
]

// 表单数据
const formData = ref({...props.service})

// 验证规则
const formRules = {
  service_name: [
    { required: true, message: '请输入渠道名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  config: [
    { required: true, message: '请输入配置json', trigger: 'blur' },
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

// get获取渠道配置
const getService = async (serviceId) => {
  try {
    const res = await axios.get(`/api/notifications/services/${serviceId}`)
    formData.value = {...res.data}
  } catch (error) {
    message.error('获取通知配置失败')
  }
}

// 显示添加对话框
const showEditDialog = async () => {
  dialogType.value = 'add'
  editingId.value = null

  await getService(formData.value.id)

  dialogVisible.value = true
}

//保存配置
const saveService = async (data) => {
  try {
    try {
      data.config = JSON.parse(data.config)
    } catch {
      message.error(`config配置有误`)
      throw new Error('config配置有误')
    }
    await axios.put(`/api/notifications/services/${data.id}`, data)

    message.success('配置成功')
  } catch (error) {
    message.error(`设置失败,${error.response?.data.detail}`)
  }
}

//变更状态
const updateServiceStatus = async () => {
  formData.value.is_enabled=!formData.value.is_enabled
  await axios.put(`/api/notifications/services/status/${formData.value.id}`, {is_enabled:formData.value.is_enabled})
  loadData()
}

// 回调
// 取消
const handleCancel = () => {
  console.log('用户取消')
}

// 提交表单
const handleSubmit = async (data) => {
  console.log('表单数据:', data)
  formData.value={...data}
  try {
      await saveService(data)
      // 刷新列表
      loadData()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}


const apiUpdateUser = async (data) => {
  // 模拟 API 调用
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, data }), 500)
  })
}

const loadData = () => {
  // 加载数据
  emit('success')
}







</script>

<style scoped>
.service-card {
  transition: all 0.3s ease;
}
.service-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-text {
  flex: 1;
}

.title {
  font-weight: 600;
  color: var(--text-color);
}

.subtitle {
  font-size: 12px;
  color: var(--text-color-2);
}

.config-form {
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}
</style>
