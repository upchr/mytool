<template>
  <n-card title="📢 通知渠道" :bordered="false" class="notify-card">
    <!-- 提示信息 -->
    <n-alert type="info" style="margin-bottom: 24px">
      <template #header>
        <n-icon><InformationCircleOutline /></n-icon>
        <span>配置说明</span>
      </template>
      配置通知渠道后，可以用于：
      <ul style="margin: 8px 0 0 0; padding-left: 20px;">
        <li>定时任务执行结果通知</li>
        <li>系统异常告警通知</li>
        <li>密码重置验证码发送</li>
        <li>工作流执行状态通知</li>
      </ul>
    </n-alert>

    <!-- 通知方式选择 -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">选择通知方式</h3>
        <n-text depth="3" class="section-subtitle">点击卡片配置通知渠道</n-text>
      </div>

      <n-grid :cols="gridCols" responsive="screen" x-gap="16" y-gap="16" class="service-grid">
        <n-grid-item v-for="service in services" :key="service.id">
          <NotificationServiceCard
            :ref="(el) => setChildMethod(service.service_type, el)"
            :class="['service-card', themeClass(service)]"
            :title="typeConfig[service.service_type]?.name"
            :subtitle="typeConfig[service.service_type]?.subtitle"
            :service="service"
            :config="getConfig(service.service_type)"
            :icon="typeConfig[service.service_type]?.icon || LinkIcon"
            @success="refreshServices"
          />
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 已配置渠道 -->
    <div class="section" v-if="enabledServices.length > 0">
      <div class="section-header">
        <h3 class="section-title">已配置渠道</h3>
        <n-tag :bordered="false" size="small" type="info">
          {{ enabledServices.length }} 个
        </n-tag>
      </div>

      <n-list bordered class="service-list">
        <n-list-item v-for="service in enabledServices" :key="service.id" class="service-list-item">
          <template #prefix>
            <div class="service-icon">
              <n-icon 
                :component="typeConfig[service.service_type]?.icon || LinkIcon" 
                :size="isMobile ? 24 : 20"
              />
            </div>
          </template>

          <div class="service-info">
            <n-space align="center" :size="8">
              <n-tag :bordered="false" type="warning" size="small">
                {{ typeConfig[service.service_type].name }}
              </n-tag>
              <n-text>{{ service.service_name }}</n-text>
            </n-space>
          </div>

          <template #suffix>
            <n-space :size="isMobile ? 12 : 8" :wrap="false" class="action-buttons">
              <n-button
                text
                :size="isMobile ? 'medium' : 'small'"
                @click="testService(service.id)"
              >
                <template #icon>
                  <n-icon :size="isMobile ? 20 : 16"><TestIcon /></n-icon>
                </template>
                <span v-if="!isMobile">测试</span>
              </n-button>
              <n-button
                text
                :size="isMobile ? 'medium' : 'small'"
                @click="editService(service)"
              >
                <template #icon>
                  <n-icon :size="isMobile ? 20 : 16"><EditIcon /></n-icon>
                </template>
                <span v-if="!isMobile">编辑</span>
              </n-button>
              <n-button
                text
                type="error"
                :size="isMobile ? 'medium' : 'small'"
                @click="disableService(service)"
              >
                <template #icon>
                  <n-icon :size="isMobile ? 20 : 16"><CloseOutline /></n-icon>
                </template>
                <span v-if="!isMobile">禁用</span>
              </n-button>
            </n-space>
          </template>
        </n-list-item>
      </n-list>

      <!-- 空状态提示 -->
      <n-empty v-if="enabledServices.length === 0" description="暂无已配置的通知渠道" />
    </div>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, markRaw, onUnmounted } from 'vue'
import { useBreakpoints } from '@vueuse/core'
import {
  LinkOutline as LinkIcon,
  LogoWechat,
  Alert,
  Book,
  Mail,
  Notifications,
  Navigate as TestIcon,
  InformationCircleOutline,
  Pencil as EditIcon,
  CloseOutline,
} from '@vicons/ionicons5'
import NotificationServiceCard from '@/components/notify/NotificationServiceCard.vue'

// 响应式断点
const breakpoints = useBreakpoints({
  mobile: 640,
  tablet: 768,
  laptop: 1024,
  desktop: 1280,
})

const isMobile = breakpoints.smaller('mobile')
const isTablet = breakpoints.between('mobile', 'laptop')

// 根据屏幕尺寸动态调整网格列数
const gridCols = computed(() => {
  if (isMobile.value) return 1
  if (isTablet.value) return 2
  return 3
})

// 服务列表
const services = ref([])

// 服务类型配置
const typeConfig = ref({
  dingtalk: {
    name: '钉钉',
    subtitle: '企业级通讯工具',
    icon: markRaw(Alert),
    config: {
      "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=..."
    }
  },
  feishu: {
    name: '飞书',
    subtitle: '协作办公平台',
    icon: markRaw(Book),
    config: {
      "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    }
  },
  bark: {
    name: 'Bark',
    subtitle: 'iOS 推送通知',
    icon: markRaw(Notifications),
    config: {
      "device_key": "xxx",
      "server_url": "https://api.day.app"
    }
  },
  email: {
    name: '邮箱',
    subtitle: '邮件通知',
    icon: markRaw(Mail),
    config: {
      "smtp_server": "...",
      "smtp_port": "587",
      "email_user": "...",
      "email_password": "...",
      "recipient_email": "..."
    }
  },
  wecom: {
    name: '企业微信',
    subtitle: '企业通讯与协作',
    icon: markRaw(LogoWechat),
    config: {
      "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
    }
  },
  webhook: {
    name: '自定义',
    subtitle: '自定义 Webhook',
    icon: markRaw(LinkIcon),
    config: {
      "webhook_url": "https://..."
    }
  },
})

// 获取配置
const getConfig = (type) => {
  return JSON.stringify(typeConfig.value[type].config || '{}')
}

// 计算已启用的服务
const enabledServices = computed(() => {
  return services.value.filter(s => s.is_enabled && s.is_configured)
})

// 子组件引用
const childRefs = ref({})

// 设置子组件方法引用
const setChildMethod = (type, el) => {
  if (el) {
    childRefs.value[type] = el
  }
}

// 显示编辑对话框
const showEditDialog = (type) => {
  if (childRefs.value[type]) {
    childRefs.value[type].showEditDialog()
  }
}

// 更新服务状态
const updateServiceStatus = (type) => {
  if (childRefs.value[type]) {
    childRefs.value[type].updateServiceStatus()
  }
}

// 测试服务
const testService = async (serviceId) => {
  try {
    await window.$request.post(`/notifications/test/${serviceId}`)
    window.$message.success('测试通知发送成功')
  } catch (error) {
    window.$message.error('测试失败')
    throw error
  }
}

// 编辑服务
const editService = (service) => {
  showEditDialog(service.service_type)
}

// 禁用服务
const disableService = async (service) => {
  updateServiceStatus(service.service_type)
}

// 检查是否已配置
const isConfigured = (config) => {
  return config && Object.keys(config).length > 0
}

// 刷新服务列表
const refreshServices = async () => {
  try {
    const data = await window.$request.get('/notifications/services')
    services.value = data.map(s => ({
      ...s,
      is_configured: isConfigured(s.config)
    }))
  } catch (error) {
    window.$message.error('刷新失败')
  }
}

// 主题样式类
const themeClass = (service) => {
  if (window.$themeStore.isDark) {
    return 'theme-dark'
  } else {
    return service.is_configured && !service.is_enabled ? 'theme-light' : ''
  }
}

// 生命周期
onMounted(() => {
  refreshServices()
})
</script>

<style scoped>
.notify-card {
  width: 100%;
}

/* 章节样式 */
.section {
  margin-bottom: 32px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  line-height: 1.5;
}

.section-subtitle {
  font-size: 14px;
}

/* 服务网格 */
.service-grid {
  margin: 0 -8px;
}

.service-card {
  border-radius: 16px;
  transition: all 0.3s ease;
  height: 100%;
}

.service-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.theme-light {
  opacity: 0.6;
}

.theme-dark {
  opacity: 0.7;
}

/* 服务列表 */
.service-list {
  border-radius: 12px;
}

.service-list-item {
  padding: 16px;
  transition: background-color 0.2s ease;
}

.service-list-item:hover {
  background-color: var(--n-color-modal);
}

.service-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.1) 0%, rgba(24, 160, 88, 0.15) 100%);
  color: #18a058;
  flex-shrink: 0;
}

.service-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.action-buttons {
  flex-shrink: 0;
  display: flex !important;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap !important;
}

.action-buttons :deep(.n-space) {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
}

.action-buttons :deep(.n-space-item) {
  display: flex !important;
  flex-shrink: 0 !important;
}

/* 移动端适配 */
@media (max-width: 640px) {
  .section {
    margin-bottom: 24px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .section-title {
    font-size: 16px;
  }

  .service-grid {
    margin: 0 -4px;
  }

  .service-list-item {
    padding: 12px;
  }

  .service-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
  }

  .service-info {
    margin-left: 12px;
  }

  .action-buttons {
    margin-left: 8px;
  }
}

@media (max-width: 480px) {
  .service-list-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .service-icon {
    display: none;
  }

  .action-buttons {
    width: 100%;
    justify-content: flex-end;
    margin-left: 0;
  }
}

/* 平板适配 */
@media (min-width: 641px) and (max-width: 1024px) {
  .section {
    margin-bottom: 28px;
  }

  .service-grid {
    margin: 0 -8px;
  }
}
</style>
