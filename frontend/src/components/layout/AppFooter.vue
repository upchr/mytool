<!-- src/components/layout/AppFooter.vue -->
<template>
  <n-layout-footer bordered class="app-footer">
    <n-flex justify="space-between" size="large">
      <span>
        <n-avatar
            style="position: fixed; left: 30px; bottom: 5px"
            @click="logoutSystem"
        >
          <n-icon :component="LogInOutline" />
        </n-avatar>
      </span>
      <span style="width: 20%">ToolsPlus.ChrPlus</span>
      <span style="padding-right: 10px">
        <n-badge processing type="warning" style="position: fixed; right: 30px; bottom: 5px">
          <n-avatar @click="goUpdate">{{ versionInfo.current }}</n-avatar>
          <template #value>
            <n-icon v-if="versionInfo.updatable" :component="UpdateIcon" />
          </template>
        </n-badge>
      </span>
    </n-flex>
  </n-layout-footer>
</template>

<script setup>
import {ref, onMounted, h} from 'vue'
import {
  CloudDownloadOutline as UpdateIcon,
  LogInOutline
} from '@vicons/ionicons5'
import {NLayoutFooter, NFlex, NAvatar, NBadge, NIcon, NButton} from 'naive-ui'
import { logoutSystem } from '@/utils/auth.js'
import {notice} from "@/utils/version/notice.js";

const versionInfo = ref({ current: '', latest: '', updatable: false, updated_at: '' })


const getVersion = async () => {
  try {
    const res = await window.$request.get('/version/')
    versionInfo.value = res
  } catch (error) {
    window.$message?.error('获取当前版本失败')
  }
}
import { useRouter } from 'vue-router'
const router = useRouter()
const goToAbout = () => {
  router.push('/versions')
}

const goUpdate = async () => {
  if (!versionInfo.value.updatable) return
  notice(versionInfo,true,goToAbout)
}

onMounted(() => {
  getVersion()
})
</script>

<style scoped>
.app-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1001;
  text-align: center;
  padding: 10px 0;
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
