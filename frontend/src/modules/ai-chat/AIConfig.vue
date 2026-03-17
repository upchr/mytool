<template>
  <div class="ai-config-container">
    <n-card title="AI 配置" class="config-card">
      <n-spin :show="loading">
        <n-form
            ref="formRef"
            :model="formData"
            :rules="rules"
            label-placement="left"
            label-width="120px"
        >
          <n-form-item label="启用 AI" path="is_enabled">
            <n-switch v-model:value="formData.is_enabled" />
            <template #feedback>
              开启后将使用配置的 AI 服务
            </template>
          </n-form-item>

          <n-form-item label="API Key" path="api_key">
            <n-input
                v-model:value="formData.api_key"
                type="password"
                show-password-on="click"
                placeholder="请输入 API Key"
                :disabled="!formData.is_enabled"
            />
            <template #feedback>
              从 AI 服务提供商获取的 API 密钥
            </template>
          </n-form-item>

          <n-form-item label="API Base URL" path="api_base">
            <n-input
                v-model:value="formData.api_base"
                placeholder="https://api.example.com/v1"
                :disabled="!formData.is_enabled"
            />
            <template #feedback>
              AI 服务的 API 基础地址
            </template>
          </n-form-item>

          <n-form-item label="模型名称" path="model">
            <n-input
                v-model:value="formData.model"
                placeholder="例如: gpt-4, claude-3"
                :disabled="!formData.is_enabled"
            />
            <template #feedback>
              要使用的 AI 模型名称
            </template>
          </n-form-item>

          <n-form-item :show-label="false">
            <div class="config-actions">
              <n-button type="primary" @click="saveConfig" :loading="saving">
                保存配置
              </n-button>
              <n-button @click="testConnection" :loading="testing" :disabled="!isFormValid">
                测试连接
              </n-button>
              <n-button @click="resetForm">
                重置
              </n-button>
            </div>
          </n-form-item>
        </n-form>

        <n-divider />

        <div class="config-info">
          <n-alert type="info" title="配置说明" :bordered="false">
            <ul>
              <li><strong>API Key:</strong> 从 AI 服务提供商的开放平台获取，例如
                <a href="https://platform.iflow.cn/profile?tab=apiKey" target="_blank" rel="noopener noreferrer">
                  iFlow 开放平台
                </a>
              </li>
              <li><strong>API Base URL:</strong> AI 服务的 API 基础地址，通常格式为 https://api.example.com/v1</li>
              <li><strong>模型名称:</strong> 具体要使用的模型，例如 gpt-4、gpt-3.5-turbo、claude-3 等</li>
              <li>配置保存后会立即生效，无需重启服务</li>
            </ul>
          </n-alert>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
import {NCard, NForm, NFormItem, NInput, NButton, NSwitch, NSpin, NDivider, NAlert, useMessage} from 'naive-ui'
import request from '@/utils/request'
import {getAuthToken} from '@/utils/auth'

const message = useMessage()
const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

const formData = ref({
  api_key: '',
  api_base: '',
  model: '',
  is_enabled: true
})

const rules = {
  api_key: {
    required: true,
    message: '请输入 API Key',
    trigger: ['blur', 'input']
  },
  api_base: {
    required: true,
    message: '请输入 API Base URL',
    trigger: ['blur', 'input'],
    pattern: /^https?:\/\/.+/,
    message: '请输入有效的 URL 地址'
  },
  model: {
    required: true,
    message: '请输入模型名称',
    trigger: ['blur', 'input']
  }
}

const isFormValid = computed(() => {
  return formData.value.api_key && formData.value.api_base && formData.value.model
})

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const token = getAuthToken()
    const res = await request.get('/ai-chat/config/detail', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (res.code === 200 && res.data) {
      formData.value = {
        api_key: res.data.api_key || '',
        api_base: res.data.api_base || '',
        model: res.data.model || '',
        is_enabled: res.data.is_enabled ?? true
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    await formRef.value?.validate()
  } catch (error) {
    return
  }

  saving.value = true
  try {
    const token = getAuthToken()
    const res = await request.post('/ai-chat/config', formData.value, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (res.code === 200) {
      message.success('配置保存成功')
    } else {
      message.error(res.message || '配置保存失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 测试连接
const testConnection = async () => {
  if (!isFormValid.value) {
    message.warning('请先填写完整的配置信息')
    return
  }

  testing.value = true
  try {
    const token = getAuthToken()
    // 临时保存配置用于测试
    await request.post('/ai-chat/config', formData.value, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    // 发送测试消息
    const testRes = await request.post('/ai-chat/chat', {
      message: '你好，这是一个测试消息',
      history: []
    }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (testRes.code === 200 && testRes.data) {
      message.success('连接测试成功！AI 响应正常')
    } else {
      message.error('连接测试失败，请检查配置')
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    message.error('测试连接失败，请检查配置和网络')
  } finally {
    testing.value = false
  }
}

// 重置表单
const resetForm = () => {
  loadConfig()
  message.info('已重置为保存的配置')
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.ai-config-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.config-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-start;
}

.config-info {
  margin-top: 20px;
}

.config-info ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.config-info li {
  margin: 8px 0;
  line-height: 1.6;
}

.config-info a {
  color: #1976d2;
  text-decoration: none;
}

.config-info a:hover {
  text-decoration: underline;
}

/* 深色模式适配 */
.dark .config-card {
  background: #1e1e1e;
}
</style>