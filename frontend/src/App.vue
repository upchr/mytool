<!-- src/App.vue -->
<template>
  <n-config-provider :hljs="hljs" :theme="themeStore.theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-space vertical style="width: 100vw">
            <AppHeader @toggle-menu="toggleMenu" />
            <n-layout has-sider class="app-layout">
              <AppSidebar v-model:collapsed="collapsed" />
              <AppContent  v-model:collapsed="collapsed" >
                <template #view>
                  <router-view />
                </template>
              </AppContent>
            </n-layout>
            <AppFooter />
            <DownloadModal
                v-model:visible="downloadModal.visible"
                :data-url="downloadModal.dataUrl"
                :filename="downloadModal.filename"
            />
          </n-space>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { zhCN, dateZhCN } from 'naive-ui'
import hljs from './plugins/hljs'
import { useThemeStore } from '@/stores/theme'

// 布局状态
const collapsed = ref(true)
const themeStore = useThemeStore()

import AppHeader from "@/components/layout/AppHeader.vue";
import AppSidebar from "@/components/layout/AppSidebar.vue";
import AppContent from "@/components/layout/AppContent.vue";
import AppFooter from "@/components/layout/AppFooter.vue";
// 下载模态框
import DownloadModal from '@/components/DownloadModal.vue'
const downloadModal = ref({
  visible: false,
  dataUrl: '',
  filename: 'export.json'
})

const initDownloadModal = () => {
  window.showDownloadModal = (dataUrl, filename = 'export.json') => {
    downloadModal.value = { visible: true, dataUrl, filename }
  }
}

const toggleMenu = () => {
  collapsed.value = !collapsed.value
}

onMounted(() => {
  initDownloadModal()
})
</script>

<style scoped>
.app-layout {
}
</style>
