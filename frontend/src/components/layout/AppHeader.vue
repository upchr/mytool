<!-- src/components/layout/AppHeader.vue -->
<template>
  <n-page-header
      :subtitle="subtitle"
      class="app-header"
      :style="{
      backgroundColor: themeStore.theme?.name === 'dark' ? 'rgb(24, 24, 28)' : 'white',
      color: themeStore.theme?.name === 'dark' ? 'white' : 'black'
    }"
  >
    <template #title>ToolsPlus</template>
    <template #avatar>
      <n-avatar src="/ICON_256.PNG" />
    </template>
    <template #extra>
      <n-button
          text
          tag="a"
          href="https://github.com/upchr/mytool/"
          target="_blank"
          style="font-size: 24px; margin-right: 10px"
      >
        <n-icon><LogoGithub /></n-icon>
      </n-button>
      <n-button
          text
          style="font-size: 24px; margin-right: 10px"
          @click="themeStore.toggleTheme"
      >
        <n-icon>
          <SunIcon v-if="themeStore.theme?.name === 'dark'" />
          <MoonIcon v-else />
        </n-icon>
      </n-button>
      <n-button text style="font-size: 24px;" @click="onToggleMenu">
        <n-icon><MenuIcon /></n-icon>
      </n-button>
    </template>
  </n-page-header>
</template>

<script setup>
import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import {
  LogoGithub,
  SunnyOutline as SunIcon,
  MoonOutline as MoonIcon,
  MenuOutline as MenuIcon
} from '@vicons/ionicons5'
import { NPageHeader, NAvatar, NButton, NIcon } from 'naive-ui'
import { useThemeStore } from '@/stores/theme'

const emit = defineEmits(['toggle-menu'])

const themeStore = useThemeStore()
const { width } = useWindowSize()

const subtitle = computed(() => {
  return width.value < 1100
      ? '猜猜怎么用。'
      : '让你的灵感有迹可循，让你的设备如臂使指。'
})

const onToggleMenu = () => {
  emit('toggle-menu')
}
</script>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1001;
  padding: 10px 20px;
  height: 50px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
