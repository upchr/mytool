<template>
  <!-- 系统初始化弹框 -->
  <n-modal v-model:show="loginStore.showInitDialog" preset="dialog" title="系统初始化">
    <template #header>
      <div class="dialog-header">
        <n-icon size="24"><LockClosedOutline /></n-icon>
        <span>系统初始化</span>
      </div>
    </template>

    <n-form ref="initFormRef" :model="initForm" :rules="initRules">
      <n-form-item path="password" label="管理员密码">
        <n-input
            v-model:value="initForm.password"
            type="password"
            placeholder="请输入至少6位密码"
            show-password-on="mousedown"
        />
      </n-form-item>

      <n-form-item path="confirmPassword" label="确认密码">
        <n-input
            v-model:value="initForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password-on="mousedown"
        />
      </n-form-item>
    </n-form>

    <template #action>
      <n-button
          type="primary"
          @click="handleInitSubmit"
          :loading="initLoading"
      >
        完成初始化
      </n-button>
    </template>
  </n-modal>

  <!-- 登录弹框 -->
  <n-modal v-model:show="loginStore.showLoginDialog" preset="dialog" title="系统登录">
    <template #header>
      <div class="dialog-header">
        <n-icon size="24"><LogInOutline /></n-icon>
        <span>系统登录</span>
      </div>
    </template>

    <n-form ref="loginFormRef" :model="loginForm" :rules="loginRules">
      <n-form-item path="password" label="密码">
        <n-input
            v-model:value="loginForm.password"
            type="password"
            placeholder="请输入管理员密码"
            show-password-on="mousedown"
            @keyup.enter="handleLoginSubmit"
        />
      </n-form-item>
    </n-form>

    <template #action>
      <n-button
          type="primary"
          @click="handleLoginSubmit"
          :loading="loginLoading"
      >
        登录
      </n-button>
    </template>
  </n-modal>
</template>

<script setup>
import {ref, onMounted, watch} from 'vue'
import { LockClosedOutline, LogInOutline } from '@vicons/ionicons5'
import {
  checkSystemInitialized,
  initializeSystem,
  loginSystem,
  getAuthToken
} from '@/utils/auth'
import { useLoginStore } from '@/stores/login.js'
const loginStore = useLoginStore()
const initFormRef = ref(null)
const loginFormRef = ref(null)
const initLoading = ref(false)
const loginLoading = ref(false)

const initForm = ref({ password: '', confirmPassword: '' })
const loginForm = ref({ password: '' })

const initRules = {
  password: [
    { required: true, message: '请输入密码', trigger: ['blur'] },
    { min: 6, message: '密码至少6位', trigger: ['blur'] }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: ['blur'] },
    {
      validator: (rule, value) => {
        if (value !== initForm.value.password) {
          return new Error('两次密码不一致')
        }
        return true
      },
      trigger: ['blur']
    }
  ]
}

const loginRules = {
  password: [{ required: true, message: '请输入密码', trigger: ['blur'] }]
}

// 处理初始化提交
const handleInitSubmit = async () => {
  try {
    debugger
    await initFormRef.value?.validate()
    initLoading.value = true

    const success = await initializeSystem(initForm.value.password)
    if (success) {
      showInitDialog.value = false
      initForm.value = { password: '', confirmPassword: '' }
      // 初始化后自动显示登录弹框
      setTimeout(() => {
        showLoginDialog.value = true
      }, 500)
    }
  } catch (error) {
    console.error('初始化失败:', error)
  } finally {
    initLoading.value = false
  }
}

// 处理登录提交
const handleLoginSubmit = async () => {
  try {
    await loginFormRef.value?.validate()
    loginLoading.value = true

    const success = await loginSystem(loginForm.value.password)
    if (success) {
      showLoginDialog.value = false
      loginForm.value = { password: '' }
      // 刷新页面或重新加载数据
      window.location.reload()
    }
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loginLoading.value = false
  }
}



// 监听全局事件
onMounted(() => {
  /*// 监听显示初始化弹框事件
  window.addEventListener('showInitDialog', () => {
    showInitDialog.value = true
  })

  // 监听显示登录弹框事件
  window.addEventListener('showLoginDialog', () => {
    showLoginDialog.value = true
  })*/

  // 页面加载时检查初始化状态
  const checkAuth = async () => {
    debugger
    const isInitialized = await checkSystemInitialized()
    const hasToken = !!getAuthToken()

    if (!isInitialized) {
      loginStore.openInitDialog()   // ✅ 直接修改 store
    } else if (!hasToken) {
      loginStore.openLoginDialog()  // ✅ 直接修改 store
    }
  }

  checkAuth()
})
</script>

<style scoped>
.dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
