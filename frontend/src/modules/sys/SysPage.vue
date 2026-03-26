<template>
  <div class="sys-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">👤 系统设置</h2>
      <p class="page-description">管理系统配置和查看运行状态</p>
    </div>

    <!-- 操作按钮区域 -->
    <div class="action-buttons">
      <n-button @click="showDialog = true" type="error" size="large" block>
        <template #icon>
          <n-icon><LockClosed /></n-icon>
        </template>
        修改密码
      </n-button>
      <n-button @click="logoutSystem" type="warning" size="large" block>
        <template #icon>
          <n-icon><LogOut /></n-icon>
        </template>
        退出登录
      </n-button>
    </div>

    <!-- 项目运行时长展示 -->
    <n-card title="📊 项目运行信息" class="runtime-card">
      <template #header-extra>
        <n-button text @click="fetchRuntimeData" :loading="loading">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </template>
      <n-descriptions bordered :column="isMobile ? 1 : 2" label-placement="left" size="medium">
        <n-descriptions-item label="启动时间">
          <span class="info-value">{{ runtimeData.startTime || '加载中...' }}</span>
        </n-descriptions-item>
        <n-descriptions-item label="当前时间">
          <span class="info-value">{{ runtimeData.currentTime || '加载中...' }}</span>
        </n-descriptions-item>
        <n-descriptions-item label="运行时长" :span="isMobile ? 1 : 2">
          <n-tag type="success" size="large" round>
            <template #icon>
              <n-icon><Time /></n-icon>
            </template>
            {{ runtimeData.runtimeStr || '加载中...' }}
          </n-tag>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
    <!-- 使用通用表单对话框 -->
    <DialogForm
        ref="dialogRef"
        dialogPreset="card"
        v-model:visible="showDialog"
        v-model:formData="formData"
        :use-field-groups="true"
        :field-groups="fieldGroups"
        :rules="formRules"
        title="系统设置"
        positive-text="保存"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="设置已保存！"
        @submit="handleSubmit"
        @field-change="handleFieldChange"
    >
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
    </DialogForm>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import { LockClosed, LogOut, Refresh, Time } from '@vicons/ionicons5'
import {logoutSystem, resetPassword} from "@/utils/auth.js";
import { useWindowSize } from '@vueuse/core'

const dialogRef = ref(null)//action按钮表单要调用dialogRef.validate子组件验证

// 响应式窗口大小
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

// 加载状态
const loading = ref(false)

// 运行时长数据
const runtimeData = ref({
  startTime: '',
  currentTime: '',
  runtimeSeconds: 0,
  runtimeStr: ''
})

// 获取运行时长数据
const fetchRuntimeData = async () => {
  try {
    loading.value = true
    const data = await window.$request.get('/sys/runtime')
    runtimeData.value = {
      startTime: data.start_time ? new Date(data.start_time).toLocaleString('zh-CN') : '',
      currentTime: data.current_time ? new Date(data.current_time).toLocaleString('zh-CN') : '',
      runtimeSeconds: data.runtime_seconds || 0,
      runtimeStr: data.runtime_str || '未知'
    }
  } catch (error) {
    console.error('获取运行时长失败:', error)
    window.$message.error('获取运行时长失败')
  } finally {
    loading.value = false
  }
}

// 定时器引用
let runtimeTimer = null

// 组件挂载时
onMounted(() => {
  // 立即获取一次数据
  fetchRuntimeData()
  // 每秒更新一次
  runtimeTimer = setInterval(fetchRuntimeData, 1000)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (runtimeTimer) {
    clearInterval(runtimeTimer)
  }
})

// 表单数据
const formData = ref({
  oldPassword: '',
  newPassword: '',
  reNewPassword: '',
})

// 字段分组配置
const fieldGroups = [
  {
    title: '旧设置',
    // description: '用于个人资料展示',
    fields: [
      {
        name: 'oldPassword',
        label: '旧密码',
        type: 'input',
        inputType:"password",
        showPasswordOn:"click",
        placeholder: '请输入旧密码',
      }
    ]
  },
  {
    title: '新设置',
    fields: [
      {
        name: 'newPassword',
        label: '新密码',
        type: 'input',
        inputType:"password",
        showPasswordOn:"click",
        placeholder: '请输入新密码',
      },
      {
        name: 'reNewPassword',
        label: '重复',
        type: 'input',
        inputType:"password",
        showPasswordOn:"click",
        placeholder: '请再次输入新密码',
      }
    ]
  }
]

// 验证规则
const formRules = (model) => ({
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: ['blur'] },
    { min: 6, message: '密码至少6位', trigger: ['blur'] }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: ['blur'] },
    { min: 6, message: '密码至少6位', trigger: ['blur'] }
  ],
  reNewPassword: [
    { required: true, message: '请再次输入新密码', trigger: ['blur'] },
    { min: 6, message: '密码至少6位', trigger: ['blur'] },
    {
      validator: (rule, value) => {
        if (value !== model.newPassword) {
          return new Error('两次密码不一致')
        }
        return true
      },
      trigger: ['blur']
    }
  ]
})


const showDialog = ref(false)


const handleCancel = () => {
  console.log('用户取消')
  showDialog.value=false//控制隐藏，card模式使用
}
// 处理提交
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
    await resetPassword(data.oldPassword,data.newPassword)
    showDialog.value=false//控制隐藏，card模式使用
    // 刷新列表
  } catch (error) {
    console.log(error)
  }
}

// 字段变更监听（用于联动）
const handleFieldChange = ({ fieldName, value }) => {
  /*console.log(`字段 ${fieldName} 变化:`, {
    值: value,
    类型: typeof value,
    是否为数字: !isNaN(Number(value))
  })*/
}

// 恢复默认
const resetToDefault = () => {
  Object.assign(formData, {
    oldPassword: '',
    newPassword: '',
    reNewPassword: '',
  })
}

// 自定义保存逻辑
const saveAndClose = (data) => {
  console.log('自定义保存:', data)
  handleSubmit(data)
  showDialog.value = false
}
</script>

<style scoped>
.sys-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--n-text-color);
}

.page-description {
  font-size: 14px;
  color: var(--n-text-color-3);
  margin: 0;
}

/* 操作按钮区域 */
.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.action-buttons :deep(.n-button) {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

/* 运行时长卡片 */
.runtime-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.runtime-card :deep(.n-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--n-divider-color);
}

.runtime-card :deep(.n-card__content) {
  padding: 24px;
}

.info-value {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: var(--n-text-color-2);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sys-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .page-description {
    font-size: 13px;
  }

  .action-buttons {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .action-buttons :deep(.n-button) {
    height: 44px;
    font-size: 15px;
  }

  .runtime-card {
    border-radius: 8px;
  }

  .runtime-card :deep(.n-card__header) {
    padding: 16px;
  }

  .runtime-card :deep(.n-card__content) {
    padding: 16px;
  }

  .runtime-card :deep(.n-descriptions-table) {
    font-size: 13px;
  }

  .info-value {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .sys-page {
    padding: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .page-description {
    font-size: 12px;
  }

  .action-buttons {
    gap: 10px;
  }

  .action-buttons :deep(.n-button) {
    height: 40px;
    font-size: 14px;
  }

  .runtime-card :deep(.n-card__header) {
    padding: 12px;
  }

  .runtime-card :deep(.n-card__content) {
    padding: 12px;
  }

  .runtime-card :deep(.n-descriptions-table) {
    font-size: 12px;
  }

  .runtime-card :deep(.n-tag) {
    font-size: 13px;
  }
}

/* 深色模式适配 */
:deep(.n-card) {
  background-color: var(--n-card-color);
  border-color: var(--n-border-color);
}

:deep(.n-descriptions) {
  --n-td-color: var(--n-modal-color);
}

:deep(.n-descriptions-table) {
  --n-th-color: var(--n-th-color);
  --n-td-text-color: var(--n-text-color);
  --n-th-text-color: var(--n-text-color-2);
}

/* 动画效果 */
.runtime-card {
  transition: all 0.3s ease;
}

.runtime-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.action-buttons :deep(.n-button) {
  transition: all 0.2s ease;
}

.action-buttons :deep(.n-button:hover) {
  transform: translateY(-2px);
}
</style>
