<!-- src/components/layout/AppSidebar.vue -->
<template>
  <!-- 桌面端侧边栏 -->
  <n-layout-sider
      ref="siderRef"
      bordered
      collapse-mode="width"
      :collapsed-width="60"
      :width="190"
      :collapsed="collapsed"
      show-trigger
      @collapse="emit('update:collapsed', true)"
      @expand="emit('update:collapsed', false)"
      class="fixed-sider"
  >
    <n-menu
        v-model:value="activeKey"
        :collapsed="collapsed"
        :collapsed-width="60"
        :collapsed-icon-size="22"
        :options="menuOptions"
    />
  </n-layout-sider>

  <!-- 移动端遮罩 + 侧边栏 -->
  <div v-if="isMobile" class="menu-container" :class="{ 'menu-open': !collapsed }">
    <div
        v-show="!collapsed"
        class="menu-overlay"
        @click="emit('update:collapsed', true)"
        @touchstart="emit('update:collapsed', true)"
    ></div>
    <n-layout-sider
        ref="siderRef"
        bordered
        collapse-mode="width"
        :collapsed-width="60"
        :width="190"
        :collapsed="collapsed"
        show-trigger
        @collapse="emit('update:collapsed', true)"
        @expand="emit('update:collapsed', false)"
        class="mobile-sider"
    >
      <n-menu
          v-model:value="activeKey"
          :collapsed="collapsed"
          :collapsed-width="60"
          :collapsed-icon-size="22"
          :options="menuOptions"
      />
    </n-layout-sider>
  </div>
</template>

<script setup>
import { ref, computed , h,} from 'vue'
import { useWindowSize } from '@vueuse/core'
import {NIcon, NLayoutSider, NMenu} from 'naive-ui'
import { RouterLink } from 'vue-router'
import { routeLabels } from '@/router/index.js'

const props = defineProps({
  collapsed: Boolean
})

const emit = defineEmits(['update:collapsed'])

const activeKey = ref(null)
const siderRef = ref(null)
const { width } = useWindowSize()

const isMobile = computed(() => width.value < 1000)

// 构建菜单项
const menuOptions = routeLabels.map(route => ({
  label: () => h(RouterLink, { to: route.path }, { default: () => route.label }),
  key: route.key,
  icon: renderIcon(route.icon)
}))

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}
</script>

<style scoped>
.fixed-sider {
  position: fixed;
  top: 50px;
  left: 0;
  bottom: 44px;
  height: calc(100vh);
  padding-bottom: 100px;
  z-index: 1000;
}

@media (max-width: 1000px) {
  .fixed-sider {
    display: none;
  }

  .menu-container {
    position: relative;
  }

  .menu-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 999;
  }

  .mobile-sider {
    position: fixed;
    top: 50px;
    bottom: 44px;
    left: 0;
    height: calc(100vh);
    padding-bottom: 100px;
    z-index: 1000;
  }
}
</style>
