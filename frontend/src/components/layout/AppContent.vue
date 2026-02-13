<!-- src/components/layout/AppContent.vue -->
<template>
  <n-layout
      class="app-content"
      :style="{
      marginLeft: collapsed ? '60px' : '200px',
      marginTop: '50px',
      marginBottom: '60px',
      padding: '20px',
      height: 'calc(100vh - 50px)'
    }"
  >
    <AuthDialogs />
    <slot name="view" />
  </n-layout>
</template>

<script setup>
import AuthDialogs from '@/components/AuthDialogs.vue'
const props = defineProps({
  collapsed: Boolean
})
</script>

<style scoped>
.app-content {
  transition: margin-left 0.3s ease;
}

@media (max-width: 1000px) {
  .app-content {
    margin-left: 5vw !important;
    margin-top: 20px !important;
  }
}
</style>
