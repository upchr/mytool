<template>
  <!-- 系统初始化弹框 -->
  <n-modal v-model:show="loginStore.showInitDialog" preset="dialog" title="系统初始化" @after-leave="closeLoginModal">
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
            show-password-on="click"
        />
      </n-form-item>

      <n-form-item path="confirmPassword" label="确认密码">
        <n-input
            v-model:value="initForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password-on="click"
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
  <n-modal v-model:show="loginStore.showLoginDialog" preset="dialog" title="系统登录" @after-leave="closeLoginModal">
    <template #header>
      <div class="dialog-header">
        <n-icon size="24"><LogInOutline /></n-icon>
        <span>系统登录</span>
      </div>
    </template>

    <n-alert v-if="loginError" type="error" :title="loginError" closable @close="loginError = ''" style="margin-bottom: 16px" />

    <n-alert v-if="remainingAttempts !== null" type="warning" style="margin-bottom: 16px">
      <template #header>
        <n-icon><WarningOutline /></n-icon>
        <span>登录尝试次数</span>
      </template>
      剩余尝试次数：{{ remainingAttempts }} / {{ maxAttempts }}
    </n-alert>

    <n-form ref="loginFormRef" :model="loginForm" :rules="loginRules">
      <n-form-item path="password" label="密码">
        <n-input
            v-model:value="loginForm.password"
            type="password"
            placeholder="请输入管理员密码"
            show-password-on="click"
            @keyup.enter="handleLoginSubmit"
        />
      </n-form-item>
    </n-form>

    <template #action>
      <n-space vertical style="width: 100%">
        <n-button
            type="primary"
            @click="handleLoginSubmit"
            :loading="loginLoading"
            block
        >
          登录
        </n-button>
        <n-button
            text
            @click="showResetPasswordDialog"
            block
        >
          忘记密码？
        </n-button>
      </n-space>
    </template>
  </n-modal>

  <!-- 重置密码弹框 -->
  <n-modal v-model:show="showResetDialog" preset="dialog" title="重置密码" @after-leave="closeResetModal">
    <template #header>
      <div class="dialog-header">
        <n-icon size="24"><KeyOutline /></n-icon>
        <span>重置密码</span>
      </div>
    </template>

    <n-alert type="info" style="margin-bottom: 16px">
      <template #header>
        <n-icon><InformationCircleOutline /></n-icon>
        <span>重置说明</span>
      </template>
      验证码将通过通知渠道发送到您配置的通知服务（企业微信、Bark、邮件等），请确保已配置并启用了至少一个通知服务。
    </n-alert>

    <n-form ref="resetFormRef" :model="resetForm" :rules="resetRules">
      <n-form-item path="code" label="验证码">
        <n-space align="center" style="width: 100%">
          <n-input
              v-model:value="resetForm.code"
              placeholder="请输入6位验证码"
              maxlength="6"
              style="flex: 1"
          />
          <n-button
              type="primary"
              @click="handleSendResetCode"
              :loading="sendCodeLoading"
              :disabled="sendCodeCooldown > 0"
              style="min-width: 120px"
          >
            {{ sendCodeCooldown > 0 ? `${sendCodeCooldown}秒` : '发送验证码' }}
          </n-button>
        </n-space>
      </n-form-item>

      <n-form-item path="newPassword" label="新密码">
        <n-input
            v-model:value="resetForm.newPassword"
            type="password"
            placeholder="请输入至少6位新密码"
            show-password-on="click"
        />
      </n-form-item>

      <n-form-item path="confirmPassword" label="确认密码">
        <n-input
            v-model:value="resetForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password-on="click"
        />
      </n-form-item>
    </n-form>

    <n-text v-if="resetCodeSent" depth="3" style="display: block; text-align: center; margin-top: 8px">
      验证码已发送，请查收通知
    </n-text>

    <template #action>
      <n-button
          type="primary"
          @click="handleVerifyResetCode"
          :loading="verifyLoading"
          block
      >
        验证并重置
      </n-button>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  LockClosedOutline, 
  LogInOutline, 
  KeyOutline, 
  WarningOutline, 
  InformationCircleOutline 
} from '@vicons/ionicons5'
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
const resetFormRef = ref(null)
const initLoading = ref(false)
const loginLoading = ref(false)
const sendCodeLoading = ref(false)
const verifyLoading = ref(false)

const initForm = ref({ password: '', confirmPassword: '' })
const loginForm = ref({ password: '' })
const resetForm = ref({ code: '', newPassword: '', confirmPassword: '' })

const loginError = ref('')
const remainingAttempts = ref(null)
const maxAttempts = ref(5)

const showResetDialog = ref(false)
const resetCodeSent = ref(false)
const sendCodeCooldown = ref(0)

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

const resetRules = {
  code: [
    { 
      validator: (rule, value) => {
        if (resetCodeSent.value && !value) {
          return new Error('请输入验证码')
        }
        if (value && value.length !== 6) {
          return new Error('验证码为6位数字')
        }
        return true
      },
      trigger: ['blur']
    }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: ['blur'] },
    { min: 6, message: '密码至少6位', trigger: ['blur'] }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: ['blur'] },
    {
      validator: (rule, value) => {
        if (value !== resetForm.value.newPassword) {
          return new Error('两次密码不一致')
        }
        return true
      },
      trigger: ['blur']
    }
  ]
}

const closeLoginModal = () => {
  initForm.value = { password: '', confirmPassword: '' }
  loginForm.value = { password: '' }
  loginError.value = ''
  remainingAttempts.value = null
}

const closeResetModal = () => {
  resetForm.value = { code: '', newPassword: '', confirmPassword: '' }
  resetCodeSent.value = false
  sendCodeCooldown.value = 0
}

const handleInitSubmit = async () => {
  try {
    await initFormRef.value?.validate()
    initLoading.value = true
    const success = await initializeSystem(initForm.value.password)
    if (success) {
      loginStore.closeInitDialog()
      initForm.value = { password: '', confirmPassword: '' }
      setTimeout(() => {
        loginStore.openLoginDialog()
      }, 500)
    }
  } catch (error) {
    console.error('初始化失败:', error)
  } finally {
    initLoading.value = false
  }
}

const handleLoginSubmit = async () => {
  try {
    await loginFormRef.value?.validate()
    loginLoading.value = true
    loginError.value = ''
    
    const result = await loginSystem(loginForm.value.password)
    
    console.log('登录结果:', result)
    
    if (result.success) {
      loginStore.closeLoginDialog()
      loginForm.value = { password: '' }
      loginError.value = ''
      remainingAttempts.value = null
      window.$message.success('登录成功！')
      console.log('准备刷新页面...')
      setTimeout(() => {
        console.log('正在刷新页面...')
        window.location.reload()
      }, 500)
    } else {
      loginError.value = result.message || '登录失败'
      
      // 从 detail 中提取剩余尝试次数
      if (result.detail) {
        const match = result.detail.match(/剩余尝试次数：(\d+)/)
        if (match) {
          remainingAttempts.value = parseInt(match[1])
        } else if (result.detail.includes('账户已锁定')) {
          remainingAttempts.value = 0
        }
      }
    }
  } catch (error) {
    console.error('登录失败:', error)
    const errorData = error.response?.data
    const msg = errorData?.message || errorData?.detail || error.message || '登录失败'
    loginError.value = msg
    
    // 从错误响应中提取剩余尝试次数
    if (errorData?.detail) {
      const match = errorData.detail.match(/剩余尝试次数：(\d+)/)
      if (match) {
        remainingAttempts.value = parseInt(match[1])
      } else if (errorData.detail.includes('账户已锁定')) {
        remainingAttempts.value = 0
      }
    }
  } finally {
    loginLoading.value = false
  }
}

const showResetPasswordDialog = () => {
  showResetDialog.value = true
}

const handleSendResetCode = async () => {
  try {
    sendCodeLoading.value = true
    
    const result = await window.$request.post('/sys/password-reset/send-code')
    
    console.log('发送验证码响应:', result)
    
    if (result && result.code) {
      resetCodeSent.value = true
      window.$message.success(result.message || '验证码已发送')
      
      window.$notification.info({
        title: '测试环境',
        content: `验证码：${result.code}`,
        duration: 10000
      })
      
      startCooldown()
    } else {
      window.$message.error('发送验证码失败')
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    const errorData = error.response?.data
    const msg = errorData?.message || errorData?.detail || '发送验证码失败'
    window.$message.error(msg)
  } finally {
    sendCodeLoading.value = false
  }
}

const handleVerifyResetCode = async () => {
  try {
    await resetFormRef.value?.validate()
    verifyLoading.value = true
    
    const result = await window.$request.post('/sys/password-reset/verify', {
      code: resetForm.value.code,
      new_password: resetForm.value.newPassword
    })
    
    console.log('验证验证码响应:', result)
    
    window.$message.success(result || '密码重置成功')
    showResetDialog.value = false
    closeResetModal()
    
    loginForm.value = { password: '' }
    loginError.value = ''
    remainingAttempts.value = null
  } catch (error) {
    console.error('验证验证码失败:', error)
    const errorData = error.response?.data
    const msg = errorData?.message || errorData?.detail || '验证验证码失败'
    window.$message.error(msg)
  } finally {
    verifyLoading.value = false
  }
}

const startCooldown = () => {
  sendCodeCooldown.value = 60
  const timer = setInterval(() => {
    sendCodeCooldown.value--
    if (sendCodeCooldown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

onMounted(() => {
  const checkAuth = async () => {
    const isInitialized = await checkSystemInitialized()
    const hasToken = !!getAuthToken()

    if (!isInitialized) {
      loginStore.openInitDialog()
    } else if (!hasToken) {
      loginStore.openLoginDialog()
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
