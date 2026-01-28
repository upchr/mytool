<template>
  <n-card title="12312">
    <!-- 添加按钮 -->
    <n-button @click="showAddDialog">
      添加用户
    </n-button>

    <!-- 编辑按钮 -->
    <n-button @click="showEditDialog(item)">
      编辑
    </n-button>

    <!-- 对话框表单组件 -->
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
          用户信息
        </div>
      </template>
      <template #icon>
        <n-icon>
          <ChatbubbleOutline />
        </n-icon>
      </template>

    </DialogForm>
  </n-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import {NIcon, useMessage} from 'naive-ui'
import {ChatbubbleOutline} from "@vicons/ionicons5";

const message = useMessage()

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
    name: 'username',
    label: '用户名',
    type: 'input',
    placeholder: '请输入用户名',
    description:'123',
  },
  {
    name: 'email',
    label: '邮箱',
    type: 'input',
    placeholder: '请输入邮箱',
  },
  {
    name: 'age',
    label: '年龄',
    type: 'number',
    placeholder: '请输入年龄',
    min: 0,
    max: 150,
  },
  {
    name: 'gender',
    label: '性别',
    type: 'select',
    placeholder: '请选择性别',
    options: [
      { label: '男', value: 'male' },
      { label: '女', value: 'female' }
    ]
  },
  {
    name: 'status',
    label: '状态',
    type: 'switch',
    checkedValue: true,
    uncheckedValue: false
  },
  {
    name: 'birthday',
    label: '生日',
    type: 'date',
    placeholder: '请选择生日'
  },
  {
    name: 'description',
    label: '描述',
    type: 'textarea',
    placeholder: '请输入描述',
    rows: 3
  },
  {
    name: 'role',
    label: '角色',
    type: 'radio',
    options: [
      { label: '用户', value: 'user' },
      { label: '管理员', value: 'admin' },
      { label: '超级管理员', value: 'superadmin' }
    ]
  }
]

// 表单数据
const formData = reactive({
  username: '',
  email: '',
  age: null,
  gender: 'male',
  status: true,
  birthday: null,
  description: '',
  role: 'user'
})

// 验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  age: [
    { type: 'number', min: 0, max: 150, message: '年龄必须在 0-150 之间', trigger: 'blur' }
  ]
}

// 重置表单数据.默认非‘’的要配置
const resetFormData = ()=>{
  // 重置表单数据
  Object.keys(formData).forEach(key => {
    if (key === 'status') {
      formData[key] = true
    } else if (key === 'gender') {
      formData[key] = 'male'
    } else if (key === 'role') {
      formData[key] = 'user'
    } else if (key === 'age') {
      formData[key] = null
    } else if (key === 'birthday') {
      formData[key] = null
    } else {
      formData[key] = ''
    }
  })
}


// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  editingId.value = null

  resetFormData()

  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (item) => {
  dialogType.value = 'edit'
  editingId.value = item.id

  // 填充表单数据
  Object.keys(formData).forEach(key => {
    formData[key] = item[key] ?? ''
  })

  dialogVisible.value = true
}


// 回调
// 取消
const handleCancel = () => {
  console.log('用户取消')
}

// 提交表单
const handleSubmit = async (data) => {
  console.log('表单数据:', data)

  try {
    if (dialogType.value === 'add') {
      // 调用添加API
      await apiAddUser(data)
      message.success('添加成功')
    } else {
      // 调用更新API
      await apiUpdateUser({ id: editingId.value, ...data })
      message.success('更新成功')
    }

    // 刷新列表
    loadData()

  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

// API 示例
const apiAddUser = async (data) => {
  // 模拟 API 调用
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, data }), 500)
  })
}

const apiUpdateUser = async (data) => {
  // 模拟 API 调用
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, data }), 500)
  })
}

const loadData = () => {
  // 加载数据
}
</script>
