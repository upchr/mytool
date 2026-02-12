<template>
  <n-card hoverable style="height: 13vh;min-height: 135px">
    <template #header>
      <n-flex justify="center" align="center">
        <n-icon :component="icon" size="24" />
        <n-flex vertical justify="center" align="center">
          <div class="title">{{ title }}</div>
          <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
        </n-flex>
      </n-flex>
    </template>
    <n-flex vertical justify="center" align="center" style="height: 100%;">
      <template v-if="!service.is_configured">
        <n-button type="info" size="small" @click="showEditDialog">
          + 配置
        </n-button>
      </template>
      <template v-else>
        <n-flex justify="center" align="center" :wrap="false">
          <n-button text size="small" @click="showEditDialog">
            <n-tag type="info">编辑</n-tag>
          </n-button>
          <n-button text size="small" @click="updateServiceStatus">
            <n-tag v-if="service.is_enabled" type="primary">已启用</n-tag>
            <n-tag v-else type="warning">已禁用</n-tag>
          </n-button>
        </n-flex>
      </template>
      <DialogForm
          ref="dialogRef"
          :dialogPreset="dialogPreset"
          v-model:visible="dialogVisible"
          v-model:formData="formData"
          type="warning"
          :title="dialogTitle(service.service_name)"
          :fields="formFields"
          :rules="formRules"
          :positive-text="dialogType === 'add' ? '添加' : '保存'"
          @submit="handleSubmit"
          @cancel="handleCancel"
          @field-change="handleFieldChange"
      >

        <template #icon>
          <n-icon>
            <ChatbubbleOutline />
          </n-icon>
        </template>
        <template #action="{ formData }">
          <!--modal预设为dialog不要用action，会覆盖默认positive-click，negative-click对应触发@submit="handleSubmit"，@cancel="handleCancel"-->
          <!--覆盖后，提交需要自己验证表单handleSubmit(formData,true)-->
          <!--未覆盖，子组件自行验证表单后emit-handleSubmit(formData)-->
          <!--获取子组件值formData：<slot name="action" :formData="localFormData"/>-->
          <n-space justify="end">
            <n-button size="small" type="default" @click="handleCancel">取消</n-button>
            <n-button size="small" type="success" @click="handleSubmit(formData,true)">确定</n-button>
          </n-space>
        </template>
        <template #footer>
          请根据对应格式填写。
        </template>
      </DialogForm>
    </n-flex>
  </n-card>
</template>

<script setup>
import { ref } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import {NIcon} from 'naive-ui'
import {ChatbubbleOutline} from "@vicons/ionicons5";

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
const dialogPreset = ref('dialog')
const dialogRef = ref(null)//action按钮表单要调用dialogRef.validate子组件验证

// 对话框状态
const dialogVisible = ref(false)
const dialogType = ref('add') // 'add' | 'edit'
const editingId = ref(null)
const item = ref(null)
// 计算标题
const dialogTitle = (name) => {
  // return dialogType.value === 'add' ? '添加渠道' : '编辑渠道'
  // return `编辑 ${name}`
  return `编辑 ${props.title}`
}

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
    placeholder: `${props.config}`,
    autosize: {
        minRows: 5,
        maxRows: 10,
    }
  },
  {
    name: 'is_enabled',
    label: '状态',
    type: 'switch',
    checkedValue: true,
    uncheckedValue: false
  }
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
    const res = await window.$request.get(`/notifications/services/${serviceId}`)
    debugger
    formData.value = {...res}
  } catch (error) {
    window.$message.error('获取通知配置失败')
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
      window.$message.error(`config配置有误`)
      throw new Error('config配置有误')
    }
    await window.$request.put(`/notifications/services/${data.id}`, data)

    window.$message.success('配置成功')
  } catch (error) {
    window.$message.error(`设置失败,${error.response?.data.detail}`)
  }
}

//变更状态
const updateServiceStatus = async () => {
  formData.value.is_enabled=!formData.value.is_enabled
  await window.$request.put(`/notifications/services/status/${formData.value.id}`, {is_enabled:formData.value.is_enabled})
  loadData()
}

// 回调
// 字段变动
const handleFieldChange = ({ fieldName, value }) => {
  // console.log(fieldName,value)
}
// 取消
const handleCancel = () => {
  console.log('用户取消')
  dialogVisible.value=false//控制隐藏，card模式使用
}

// 提交表单
const handleSubmit = async (data,flag=false) => {
  if(flag){//自定义按钮时，验证表单
    if (dialogRef.value) {
      try {
        await dialogRef.value.validate()
        console.log('✅ 表单验证通过')
      } catch (error) {
        console.log('❌ 表单验证失败:', error)
        return
      }
    }
  }



  formData.value={...data}
  try {
      await saveService(data)
      dialogVisible.value=false//控制隐藏，card模式使用
      // 刷新列表
      loadData()
  } catch (error) {
    window.$message.error(error.message || '操作失败')
  }
}

const loadData = () => {
  // 加载数据
  emit('success')
}

//提供父组件调用方法
defineExpose({
  showEditDialog,
  updateServiceStatus,
})
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
@media (max-width: 1000px) {
  .title {
    font-size: 13px;
  }
}

.subtitle {
  font-size: 12px;
  color: var(--text-color-2);
}
@media (max-width: 1000px) {
  .subtitle {
    font-size: 10px;
  }
}
.config-form {
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}
</style>
