<template>
  <div class="min-h-screen bg-gray-50" style="margin-left: 5vw;margin-right: 5vw">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"  style="text-align: center;font-size: 20px">
        <div class="flex justify-between h-16">
          <div class="flex">
            <router-link to="/" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md">
              <span class="font-bold text-lg">📝 便签管理</span>
            </router-link>
            <router-link to="/nodes" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md ml-4">
              <span class="font-bold text-lg">🖥️ 节点管理</span>
            </router-link>
            <router-link to="/jobs" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md ml-4">
              <span class="font-bold text-lg">⏰ 任务管理</span>
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <main class="flex-1 py-6">
      <n-message-provider>
          <router-view />
      </n-message-provider>
<!--      <router-view />-->
    </main>

    <footer
        class="bg-white shadow-inner fixed bottom-0 left-0 right-0"
        style="text-align: center; z-index: 10;"
    >
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
        © 2026 定时任务管理系统
      </div>
    </footer>
  </div>

</template>

<script setup>
import { RouterView } from 'vue-router'
</script>
