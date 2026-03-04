<!-- CertificateDetail.vue -->
<template>
  <n-modal class="mediaModal "
      v-model:show="showModal"
      preset="card"
      :title="`证书详情 - ID: ${certData?.id || ''}`"
      style="width: 750px"
      :bordered="false"
      :segmented="false"
      @after-leave="handleAfterLeave"
  >
    <n-descriptions v-if="certData" :column="2" label-placement="left" bordered>
      <n-descriptions-item label="ID">{{ certData.id }}</n-descriptions-item>
      <n-descriptions-item label="算法">{{ certData.algorithm }}</n-descriptions-item>

      <n-descriptions-item label="颁发者">{{ certData.issuer || '-' }}</n-descriptions-item>
      <n-descriptions-item label="状态">
        <n-tag :type="certData.is_active ? 'success' : 'error'" size="small">
          {{ certData.is_active ? '有效' : '已失效' }}
        </n-tag>
      </n-descriptions-item>

      <n-descriptions-item label="生效时间">
        {{ formatDate(certData.not_before) }}
      </n-descriptions-item>
      <n-descriptions-item label="过期时间">
        <span :style="{ color: isExpiringSoon(certData.not_after) ? '#d03050' : 'inherit' }">
          {{ formatDate(certData.not_after) }}
          <n-tag
              v-if="isExpiringSoon(certData.not_after)"
              type="warning"
              size="tiny"
              round
              style="margin-left: 4px;"
          >
            即将过期
          </n-tag>
        </span>
      </n-descriptions-item>

      <n-descriptions-item label="域名列表" :span="2">
        <n-space wrap :size="4">
          <n-tag
              v-for="domain in certData.domains"
              :key="domain"
              size="small"
              type="info"
              bordered
          >
            {{ domain }}
          </n-tag>
        </n-space>
      </n-descriptions-item>

      <n-descriptions-item label="证书路径" :span="2">
        <n-ellipsis style="max-width: 550px">
          {{ certData.cert_path || '-' }}
        </n-ellipsis>
      </n-descriptions-item>

      <n-descriptions-item label="证书内容" :span="2">
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: flex-end;">
            <n-button
                type="info"
                size="small"
                @click="copyHandle(certData.cert)"
                :disabled="!certData.cert"
            >
              复制证书
            </n-button>
          </div>
          <n-input
              type="textarea"
              :autosize="{
              minRows: 4,
              maxRows: 8,
            }"
              v-model:value="certData.cert"
              readonly
              placeholder="暂无证书内容"
              style="font-family: monospace; font-size: 12px;"
          />
        </div>
      </n-descriptions-item>

      <n-descriptions-item label="私钥路径" :span="2">
        <n-ellipsis style="max-width: 550px">
          {{ certData.key_path || '-' }}
        </n-ellipsis>
      </n-descriptions-item>

      <n-descriptions-item label="私钥内容" :span="2">
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: flex-end;">
            <n-button
                type="info"
                size="small"
                @click="copyHandle(certData.key)"
                :disabled="!certData.key"
            >
              复制私钥
            </n-button>
          </div>
          <n-input
              type="textarea"
              :autosize="{
              minRows: 4,
              maxRows: 8,
            }"
              v-model:value="certData.key"
              readonly
              placeholder="暂无秘钥内容"
              style="font-family: monospace; font-size: 12px;"
          />
        </div>
      </n-descriptions-item>

      <n-descriptions-item v-if="certData.fullchain_content" label="完整链" :span="2">
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: flex-end;">
            <n-button
                type="info"
                size="small"
                @click="copyHandle(certData.fullchain_content)"
            >
              复制完整链
            </n-button>
          </div>
          <n-input
              type="textarea"
              :autosize="{
              minRows: 3,
              maxRows: 6,
            }"
              v-model:value="certData.fullchain_content"
              readonly
              style="font-family: monospace; font-size: 12px;"
          />
        </div>
      </n-descriptions-item>

      <n-descriptions-item label="创建时间">
        {{ formatDate(certData.created_at) }}
      </n-descriptions-item>
      <n-descriptions-item label="下载次数">
        {{ downloadCount }}
        <n-button text type="primary" size="tiny" @click="loadDownloadCount(certData.id)">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
        </n-button>
      </n-descriptions-item>
    </n-descriptions>

    <template #footer>
      <n-space justify="end">
        <n-button @click="handleClose">关闭</n-button>
        <n-button
            type="primary"
            @click="handleDownload"
            :loading="downloading"
        >
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          下载证书
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NModal, NDescriptions, NDescriptionsItem,
  NTag, NSpace, NEllipsis, NInput,
  NButton, NIcon
} from 'naive-ui'
import { RefreshOutline, DownloadOutline } from '@vicons/ionicons5'

const props = defineProps({
  id: [String, Number],
  visible: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close', 'update:visible'])

const route = useRoute()
const router = useRouter()

const showModal = ref(props.visible)
const certData = ref(null)
const downloadCount = ref(0)
const downloading = ref(false)

// 监听 visible prop
watch(() => props.visible, (val) => {
  showModal.value = val
})

// 监听 showModal
watch(showModal, (val) => {
  emit('update:visible', val)
})

// 加载证书数据
const loadCertificate = async () => {
  const certId = props.id || route.params.id
  if (!certId) return

  try {
    const res = await window.$request.get(`/ssl/certificates/${certId}`)
    certData.value = res
    await loadDownloadCount(certId)
  } catch (error) {
    console.error('加载证书失败:', error)
    window.$message.error('加载证书失败')
  }
}

// 加载下载次数
const loadDownloadCount = async (certId) => {
  try {
    const res = await window.$request.get(`/ssl/certificates/${certId}/downloads/count`)
    downloadCount.value = res || 0
  } catch (error) {
    console.error('加载下载次数失败:', error)
    downloadCount.value = 0
  }
}

// 下载证书
const handleDownload = async () => {
  if (!certData.value) return

  // downloading.value = true
  // try {
  //   const res = await window.$request.post(`/ssl/certificates/${certData.value.id}/download`)
  //   window.$message.success('下载成功')
  //   await loadDownloadCount(certData.value.id)
  // } catch (error) {
  //   window.$message.error('下载失败')
  // } finally {
  //   downloading.value = false
  // }

  try {
    await window.$request.exportFile(`/ssl/certificates/${certData.value.id}/download-zip`, {}, `cert.zip`);
  } catch (error) {
    window.$message.error(`导出失败`)
  }
}

// 复制内容
const copyHandle = (text) => {
  if (!text) {
    window.$message.warning('没有可复制的内容')
    return
  }
  window.$copyCode(text)
}

// 关闭
const handleClose = () => {
  showModal.value = false
  emit('close')

  // 如果有路由参数，返回上一页
  if (route.params.id) {
    // 方式1：返回上一页（最稳妥）
    router.back()

    // 方式2：根据当前路径动态返回
    // const parentPath = route.path.split('/').slice(0, -2).join('/')
    // router.push(parentPath || '/ssl-apply')
  }
}

// 对话框关闭后的处理
const handleAfterLeave = () => {
  certData.value = null
  downloadCount.value = 0
  handleClose()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 判断是否即将过期
const isExpiringSoon = (dateStr) => {
  if (!dateStr) return false
  const expDate = new Date(dateStr)
  const now = new Date()
  const daysLeft = Math.floor((expDate - now) / (1000 * 60 * 60 * 24))
  return daysLeft <= 30 && daysLeft > 0
}

onMounted(() => {
  loadCertificate()
})

// 监听 id 变化
watch(() => props.id, () => {
  loadCertificate()
})
</script>
