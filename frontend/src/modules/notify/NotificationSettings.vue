<template>
  <n-card title="通知渠道" :bordered="false">
    <div class="mb-6">
      <h3 class="text-lg font-medium mb-3">选择通知方式</h3>
      <n-grid cols="1 s:2 m:3 l:4" responsive="screen">
        <n-grid-item v-for="service in services" style="margin: 10px;"
                     :key="service.id">
          <NotificationServiceCard
              style="border-radius: 15px"
              :class="['disableNotify', themeClass(service)]"
              :title="typeConfig[service.service_type]?.name"
              :subtitle="typeConfig[service.service_type]?.subtitle"
              :service="service"
              :config="getConfig(service.service_type)"
              :icon="typeConfig[service.service_type]?.icon||LinkIcon"
              @success="refreshServices"
          />
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 已配置渠道 -->
    <div class="mt-8">
      <h3 class="text-lg font-medium mb-3">已配置渠道</h3>
      <n-list>
        <n-list-item v-for="service in enabledServices" :key="service.id">
          <template #prefix>
            <n-icon :component="typeConfig[service.service_type]?.icon||LinkIcon" size="20" />
          </template>
          <span>{{ service.service_name }}</span>

          <template #suffix>
            <n-space style="width: 10vw;" justify="space-around">
              <n-button
                  text
                  size="small"
                  @click="testService(service.service_type)"
              >
                <n-icon><SendOutline /></n-icon>
                测试
              </n-button>
              <n-button
                  text
                  size="small"
                  @click="editService(service)"
              >
                <n-icon><SendOutline /></n-icon>
                编辑
              </n-button>
              <n-button
                  text
                  size="small"
                  @click="disableService(service.id)"
              >
                <n-icon><CloseOutline /></n-icon>
                禁用
              </n-button>
            </n-space>
          </template>
        </n-list-item>
      </n-list>
    </div>
  </n-card>
</template>

<script setup>
import {ref, computed, onMounted, markRaw} from 'vue'
import {
  LinkOutline as LinkIcon,
  StarOutline,
  SendOutline,
  CloseOutline,
} from '@vicons/ionicons5'
import NotificationServiceCard from '@/components/notify/NotificationServiceCard.vue'
import axios from 'axios'
import { useMessage } from 'naive-ui'

const message = useMessage()

// 服务
const services = ref([
  {
    "id": 1,
    "service_type": "wecom",
    "service_name": "企业微信",
    "is_enabled": false,
    "config": {},
    "created_at": "2026-01-28T03:08:10",
    "updated_at": "2026-01-28T03:08:10"
  }
])
// config提示配置
const typeConfig = ref({
  dingtalk: {
    name: '钉钉',
    subtitle: '1231',
    icon: markRaw(StarOutline),
    config: {"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=..."}
  },
  feishu: {
    name: '飞书',
    subtitle: '',
    icon: markRaw(StarOutline),
    config: {"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/..."}
  },
  bark: {
    name: 'Bark',
    subtitle: '',
    icon: markRaw(StarOutline),
    config: {"device_key": "xxx", "server_url": "https://api.day.app"}
  },
  email: {
    name: 'QQ邮箱',
    subtitle: '',
    icon: markRaw(StarOutline),
    config: {"smtp_server": "...", "smtp_port": "587", "email_user": "...", "email_password": "...", "recipient_email": "..."}
  },
  wecom: {
    name: '企业微信',
    subtitle: '',
    icon: markRaw(StarOutline),
    config: {"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."}
  },
  webhook: {
    name: '自定义',
    subtitle: '',
    icon: markRaw(StarOutline),
    config: {"webhook_url": "https://..."}
  },
})

// 获取服务对象
const getService = (id) => services.value.find(s => s.id === id)
//配置
const getConfig = (type) => {
  return JSON.stringify(typeConfig.value[type].config || '{}')
}

// 计算已启用的服务
const enabledServices = computed(() => {
  return services.value.filter(s => s.is_enabled)
})

// 操作方法
const openConfigModal = (serviceId) => {
  const service = getService(serviceId)
  service.is_configured = true
}


const testService = async (serviceId) => {
  try {
    await axios.post(`/api/notifications/test/${serviceId}`)
    message.success('测试通知发送成功')
  } catch (error) {
    message.error('测试失败')
  }
}


const setAsDefault = async (serviceId) => {
  try {
    await axios.put('/api/notifications/default-service', { default_service_id: serviceId })
    // 更新本地状态
    services.value.forEach(s => s.is_default = s.id === serviceId)
    message.success('已设为默认通知服务')
  } catch (error) {
    message.error('设置失败')
  }
}

const disableService = async (serviceId) => {
  const service = getService(serviceId)
  service.is_enabled = false
  service.is_configured = false
  message.success(`${service.service_name} 已禁用`)
}

const editService = (service) => {
  openConfigModal(service.id)
}
const isConfigured = (config) => {
  return config && Object.keys(config).length > 0
}
const refreshServices = async () => {
  try {
    const res = await axios.get('/api/notifications/services')
    // 更新本地状态
    services.value = res.data.services.map(s => ({
      ...s,
      is_default: s.id === res.data.default_service_id,
      is_configured: isConfigured(s.config)
    }))
  } catch (error) {
    message.error('刷新失败')
  }
}
const themeClass = (service) =>{
  if(window.$themeStore.isDark){
    return 'theme-dark'
  }else{
    return service.is_configured && !service.is_enabled ? 'theme-light' :''
  }
}

onMounted(() => {
  refreshServices()
})
</script>

<style scoped>

.mb-6 {
  margin-bottom: 24px;
}

.text-lg {
  font-size: 1.125rem;
}

.font-medium {
  font-weight: 600;
}


.disableNotify.theme-light {
  background-color: #e8e8e8;
}
.disableNotify.theme-dark {
  background-color: #1a1a1a;
}

</style>
