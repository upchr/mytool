<template>
  <div style="padding: 20px">
    <h2>👤 用户设置</h2>
    <n-space vertical style="margin-top: 10px ">
      <n-button @click="showDialog = true" type="error">修改密码</n-button>
      <n-button @click="logoutSystem" type="warning">退出登录</n-button>
    </n-space>
    <!-- 使用通用表单对话框 -->
    <DialogForm
        ref="dialogRef"
        dialogPreset="card"
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
import { ref, reactive } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import {logoutSystem, resetPassword} from "@/utils/auth.js";
const dialogRef = ref(null)//action按钮表单要调用dialogRef.validate子组件验证

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
