<template>
  <div style="padding: 20px">
    <h2>用户设置</h2>
    <n-space vertical style="margin-top: 10px ">
      <n-button @click="showDialog = true" type="error">修改密码</n-button>
      <n-button @click="logoutSystem" type="warning">退出登录</n-button>
    </n-space>
    <!-- 使用通用表单对话框 -->
    <DialogForm
        v-model:visible="showDialog"
        v-model:formData="formData"
        :use-field-groups="true"
        :field-groups="fieldGroups"
        :rules="formRules"
        title="用户设置"
        positive-text="保存"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="设置已保存！"
        @submit="handleSubmit"
        @field-change="handleFieldChange"
    >
    </DialogForm>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import {logoutSystem, resetPassword} from "@/utils/auth.js";

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
        placeholder: '请输入新密码',
      },
      {
        name: 'reNewPassword',
        label: '重复',
        type: 'input',
        placeholder: '请再次输入新密码',
      }
    ]
  }
]

// 验证规则
const formRules = (model) => ({
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: ['blur'] }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: ['blur'] }
  ],
  reNewPassword: [
    { required: true, message: '请再次输入新密码', trigger: ['blur'] },
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



// 处理提交
const handleSubmit = async (data) => {
  console.log('表单提交:', data)
  await resetPassword(data.oldPassword,data.newPassword)
  // 这里可以调用 API 保存数据
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
