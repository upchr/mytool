<template>
  <n-card title="📢  通知渠道" :bordered="false">
    <div class="mb-6">
      <h3 class="text-lg font-medium mb-3">选择通知方式</h3>
      <n-grid cols="1 s:2 m:3 l:4" responsive="screen">
        <n-grid-item v-for="service in services" style="margin: 10px;"
                     :key="service.id">
          <NotificationServiceCard
              :ref="(el) => setChildMethod(service.service_type,el)"
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
          <span>
            <n-tag type="warning">
              {{ typeConfig[service.service_type].name}}
            </n-tag>
            {{service.service_name }}</span>

          <template #suffix>
            <n-space style="width: 10vw;" justify="space-around">
              <n-button text size="small" @click="testService(service.id)">
                <n-icon><TestIcon /></n-icon>
                测试
              </n-button>
              <n-button text size="small" @click="editService(service)">
                <n-icon><EditIcon /></n-icon>
                编辑
              </n-button>
              <n-button text size="small" @click="disableService(service)">
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
  LogoWechat,Alert,
  Book,
  Mail,
  Notifications,
  Navigate as TestIcon,
  Pencil as EditIcon,
  CloseOutline,
} from '@vicons/ionicons5'
import NotificationServiceCard from '@/components/notify/NotificationServiceCard.vue'

// 服务
const services = ref([
])
// config提示配置
const typeConfig = ref({
  dingtalk: {
    name: '钉钉',
    subtitle: '1231',
    icon: markRaw(Alert),
    config: {"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=..."}
  },
  feishu: {
    name: '飞书',
    subtitle: '',
    icon: markRaw(Book),
    config: {"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/..."}
  },
  bark: {
    name: 'Bark',
    subtitle: '',
    icon: markRaw(Notifications),
    config: {"device_key": "xxx", "server_url": "https://api.day.app"}
  },
  email: {
    name: 'QQ邮箱',
    subtitle: '',
    icon: markRaw(Mail),
    config: {"smtp_server": "...", "smtp_port": "587", "email_user": "...", "email_password": "...", "recipient_email": "..."}
  },
  wecom: {
    name: '企业微信',
    subtitle: '',
    icon: markRaw(LogoWechat),
    config: {"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."}
  },
  webhook: {
    name: '自定义',
    subtitle: '',
    icon: markRaw(LinkIcon),
    config: {"webhook_url": "https://..."}
  },
})

//配置
const getConfig = (type) => {
  return JSON.stringify(typeConfig.value[type].config || '{}')
}

// 计算已启用的服务
const enabledServices = computed(() => {
  return services.value.filter(s => s.is_enabled && s.is_configured)
})



const testService = async (serviceId) => {
  try {
    await window.$request.post(`/notifications/test/${serviceId}`)
    window.$message.success('测试通知发送成功')
  } catch (error) {
    window.$message.error('测试失败')
    throw error
  }
}


// 调用子组件方法
const childRefs = ref({})
const setChildMethod = (type,el)=>{
  childRefs.value[type]=el
}
const showEditDialog = (type) => {
  if (childRefs.value[type]) {
    childRefs.value[type].showEditDialog()
  }
}
const updateServiceStatus = (type) => {
  if (childRefs.value[type]) {
    childRefs.value[type].updateServiceStatus()
  }
}



const editService = (service) => {
  showEditDialog(service.service_type)
}
const disableService = async (service) => {
  updateServiceStatus(service.service_type)
}

const isConfigured = (config) => {
  return config && Object.keys(config).length > 0
}
const refreshServices = async () => {
  try {
    const data = await window.$request.get('/notifications/services')

    // 更新本地状态
    services.value = data.map(s => ({
      ...s,
      is_configured: isConfigured(s.config)
    }))
  } catch (error) {
    window.$message.error('刷新失败')
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
