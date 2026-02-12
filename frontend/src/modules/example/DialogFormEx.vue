<template>
  <div style="padding: 20px">
    <h2>示例</h2>
    <p>当前主题: {{ themeStore.isDark? 'dark':'sun'}}</p>
    <n-space>
      <n-button @click="showDialog = true" type="primary">打开对话框</n-button>
      <n-button @click="test" type="primary">当前路径</n-button>
      <n-button @click="test404" type="primary">404异常</n-button>
      <n-button @click="testyw" type="primary">业务异常{{testRef}}</n-button>
    </n-space>
    <!-- 使用通用表单对话框 -->
    <DialogForm
        v-model:visible="showDialog"
        v-model:form-data="formData"
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
      <!-- 自定义底部按钮 -->
      <template #footer="{ formData }">
        <n-space justify="start">
          <n-button @click="resetToDefault">恢复默认</n-button>
          <n-button type="primary" @click="saveAndClose(formData)">保存并关闭</n-button>
        </n-space>
      </template>
<!--      <template #action="{ formData }">
        &lt;!&ndash;覆盖对话框默认&ndash;&gt;
        <n-button @click="resetToDefault">恢复默认</n-button>
        <n-button type="primary" @click="saveAndClose(formData)">保存并关闭</n-button>
      </template>-->
    </DialogForm>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import DialogForm from '@/components/DialogForm.vue'
import { useThemeStore } from '@/stores/theme'
const themeStore = useThemeStore()
// 表单数据
const formData = reactive({
  name: '张三',
  email: 'zhangsan@example.com',
  age: 28,
  theme: 'dark',
  language: 'zh-CN',
  notifyMethods: ['email'],
  enableNotifications: true,
  birthday: new Date('1995-08-15').getTime(),
  bio: '热爱编程，喜欢开源项目。',
  avatar: [],
  tags: ['developer', 'vue'],
  rating: 4,
  volume: 70,
  schedule: '0 8 * * *'
})

// 字段分组配置
const fieldGroups = [
  {
    title: '基本信息',
    description: '用于个人资料展示',
    fields: [
      {
        name: 'name',
        label: '姓名',
        type: 'input',
        placeholder: '请输入真实姓名',
        maxlength: 20,
        showCount: true
      },
      {
        name: 'email',
        label: '邮箱',
        type: 'input',
        inputType: 'email',
        placeholder: '用于接收通知'
      },
      {
        name: 'age',
        label: '年龄',
        type: 'number',
        min: 1,
        max: 120,
        precision: 0
      },
      {
        name: 'birthday',
        label: '生日',
        type: 'date',
        valueFormat: 'yyyy-MM-dd'
      }
    ]
  },
  {
    title: '偏好设置',
    fields: [
      {
        name: 'theme',
        label: '主题',
        type: 'select',
        options: [
          { label: '浅色', value: 'light' },
          { label: '深色', value: 'dark' },
          { label: '自动', value: 'auto' }
        ]
      },
      {
        name: 'language',
        label: '语言',
        type: 'select',
        filterable: true,
        options: [
          { label: '简体中文', value: 'zh-CN' },
          { label: 'English', value: 'en-US' },
          { label: '日本語', value: 'ja-JP' }
        ]
      },
      {
        name: 'bio',
        label: '个人简介',
        type: 'textarea',
        rows: 3,
        maxlength: 200,
        showCount: true
      }
    ]
  },
  {
    title: '通知设置',
    fields: [
      {
        name: 'enableNotifications',
        label: '启用通知',
        type: 'switch'
      },
      {
        name: 'notifyRadios',
        label: '通知方式1',
        type: 'radio',
        options: [
          { label: '邮件', value: 'email' },
          { label: '短信', value: 'sms' },
          { label: '站内信', value: 'in-app' }
        ]
      },
      {
        name: 'notifyMethods',
        label: '通知方式2',
        type: 'checkbox',
        options: [
          { label: '邮件', value: 'email' },
          { label: '短信', value: 'sms' },
          { label: '站内信', value: 'in-app' }
        ]
      }
    ]
  },
  {
    title: '高级选项',
    visible: true, // 可动态控制
    fields: [
      {
        name: 'avatar',
        label: '头像',
        type: 'upload',
        action: '/api/upload',  // 必须指定上传地址
        multiple: true,
        accept: '.jpg,.png,.pdf,.doc,.docx',
        listType: 'image-card',  // text, image, image-card
        max: 1,
        showPreviewButton: true,
        // 可以自定义上传请求头
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        // 上传前验证
        beforeUpload: ({ file }) => {
          if (file.file.size > 10 * 1024 * 1024) {
            window.$message.error('文件不能超过10MB')
            return false
          }
          return true
        }
      },
      {
        name: 'tags',
        label: '标签',
        type: 'dynamic',
        placeholder: '输入标签后按回车'
      },
      {
        name: 'rating',
        label: '满意度',
        type: 'rate'
      },
      {
        name: 'volume',
        label: '音量',
        type: 'slider',
        min: 0,
        max: 100
      },
      {
        name: 'schedule',
        label: '定时任务',
        type: 'input',
        placeholder: 'Cron 表达式，如 0 8 * * *'
      }
    ]
  }
]

// 验证规则
const formRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, message: '姓名至少2个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  age: [
    {
      type: 'number',
      required: true,
      message: '请输入年龄',
      trigger: ['blur', 'change']
    }
  ]
}

const showDialog = ref(false)


const getUsers = async ()=> {
  return window.$request.get('/example/health')

  /*return window.$request({
    url: '/example/health',
    method: 'get'
  })*/
}
const test = async () => {
  const res = await getUsers()
  console.log(res)
  window.$message.info(JSON.stringify(res))
}
const test404 = async () => {
  return window.$request.get('/example/health2')
}
const testRef = ref(0)
const testyw = async () => {
  testRef.value += 1
  return window.$request.get(`/example/health/${testRef.value}`)
}

// 处理提交
const handleSubmit = (data) => {
  console.log('表单提交:', data)

  // 这里可以调用 API 保存数据
}

// 字段变更监听（用于联动）
const handleFieldChange = ({ fieldName, value }) => {
  if (fieldName === 'theme') {
    console.log('主题切换为:', value)
    // 可以在这里触发动态主题切换
  }
  console.log(`字段 ${fieldName} 变化:`, {
    值: value,
    类型: typeof value,
    是否为数字: !isNaN(Number(value))
  })

}

// 恢复默认
const resetToDefault = () => {
  Object.assign(formData, {
    name: '张三',
    email: 'zhangsan@example.com',
    age: 28,
    theme: 'dark',
    language: 'zh-CN',
    notifyMethods: ['email'],
    enableNotifications: true,
    birthday: new Date('1995-08-15').getTime(),
    bio: '热爱编程，喜欢开源项目。',
    avatar: [],
    tags: ['developer', 'vue'],
    rating: 4,
    volume: 70,
    schedule: '0 8 * * *'
  })
}

// 自定义保存逻辑
const saveAndClose = (data) => {
  console.log('自定义保存:', data)
  handleSubmit(data)
  showDialog.value = false
}
</script>
